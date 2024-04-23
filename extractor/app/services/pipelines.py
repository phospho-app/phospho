import time
from typing import List, Literal, Optional

from loguru import logger

from app.core import config
from app.db.models import Eval, Event, EventDefinition, LlmCall, Task
from app.db.mongo import get_mongo_db
from app.services.data import fetch_previous_tasks
from app.services.projects import get_project_by_id
from app.services.predictions import create_prediction

# from app.services.topics import extract_topics  # TODO
from app.services.webhook import trigger_webhook
from phospho import lab

from app.api.v1.models.pipelines import PipelineResults


class EventConfig(lab.JobConfig):
    event_name: str
    event_description: str


async def task_event_detection_pipeline(
    task: Task, save_task: bool = True
) -> List[Event]:
    """
    Run the event detection pipeline for a given task
    """
    logger.info(f"Run the event detection pipeline for task {task.id}")
    mongo_db = await get_mongo_db()

    # Get the data of all the tasks before task[task_id]
    previous_tasks = await fetch_previous_tasks(task.id)
    task_data = previous_tasks[-1]
    if len(previous_tasks) > 1:
        task_context = previous_tasks[:-1]
    else:
        task_context = []

    # Get the project settings
    project_id = task_data.project_id
    project = await get_project_by_id(project_id)
    if project.settings is None:
        logger.warning(f"Project with id {project_id} has no settings")
        return []
    # Convert to the proper lab project object
    # TODO : Normalize the project definition by storing all db models in the phospho module
    # and importing models from the phospho module
    workload = lab.Workload.from_phospho_project_config(project)
    logger.debug(f"Workload for project {project_id} : {workload}")

    message = lab.Message.from_task(task=task_data, previous_tasks=task_context)
    latest_message_id = message.id
    await workload.async_run(
        messages=[message],
        executor_type="parallel_jobs",
    )

    # Check the results of the workload
    message_results = workload.results.get(latest_message_id, [])
    detected_events = []
    for event_name, result in message_results.items():
        # Store the LLM call in the database
        metadata = result.metadata
        llm_call = metadata.get("llm_call", None)
        if llm_call is not None:
            llm_call_obj = LlmCall(
                **llm_call,
                org_id=task_data.org_id,
                task_id=task.id,
                job_id=result.job_id,
            )
            mongo_db["llm_calls"].insert_one(llm_call_obj.model_dump())
        else:
            logger.warning(f"No LLM call detected for event {event_name}")

        # When the event is detected, result is True
        if result.value:
            logger.info(f"Event {event_name} detected for task {task_data.id}")
            # Get back the event definition from the job metadata
            metadata = workload.jobs[result.job_id].metadata
            event = EventDefinition(**metadata)
            # Push event to db
            detected_event_data = Event(
                event_name=event_name,
                # Events detected at the session scope are not linked to a task
                task_id=task_data.id,
                session_id=task_data.session_id,
                project_id=project_id,
                source=result.metadata.get("source", "phospho-unknown"),
                webhook=event.webhook,
                org_id=task_data.org_id,
                event_definition=event,
                task=task_data if not save_task else None,
            )
            detected_events.append(detected_event_data)
            # Update the task object with the event
            if save_task:
                mongo_db["tasks"].update_many(
                    {"id": task.id, "project_id": task.project_id},
                    # Add the event to the list of events
                    {"$push": {"events": detected_event_data.model_dump()}},
                )
            # Trigger the webhook if it exists
            if event.webhook is not None:
                await trigger_webhook(
                    url=event.webhook,
                    json=detected_event_data.model_dump(),
                    headers=event.webhook_headers,
                )

        # Save the prediction
        # Get the event object from the settings
        event_settings = project.settings.events[event_name]

        # Get the job_id from the event
        job_id = event_settings.job_id

        if job_id is None:
            logger.error(f"No job_id found for event {event_name}")

        else:
            prediction = await create_prediction(
                project.org_id,
                project_id,
                job_id,
                result.value,
                "event_detection",
                task_id=task.id,
            )

    if len(detected_events) > 0:
        mongo_db["events"].insert_many(
            [event.model_dump() for event in detected_events]
        )
    return detected_events


async def task_scoring_pipeline(
    task: Task, save_task: bool = True
) -> Optional[Literal["success", "failure"]]:
    """
    Run the task scoring pipeline for a given task
    """
    logger.debug(f"Run the task scoring pipeline for task {task.id}")
    mongo_db = await get_mongo_db()

    # We want 50/50 success and failure examples
    nb_success = int(config.FEW_SHOT_MAX_NUMBER_OF_EXAMPLES / 2)
    nb_failure = int(config.FEW_SHOT_MAX_NUMBER_OF_EXAMPLES / 2)

    PHOSPHO_EVAL_MODELS_NAMES = ["phospho", "phospho-4"]

    # Get the user evals from the db
    successful_examples_tasks = (
        await mongo_db["evals"]
        .aggregate(
            [
                {
                    "$match": {
                        "project_id": task.project_id,
                        "source": {"$nin": PHOSPHO_EVAL_MODELS_NAMES},
                        "value": "success",
                    }
                },
                {"$sort": {"created_at": -1}},
                {"$limit": nb_success},
                {
                    "$lookup": {
                        "from": "tasks",
                        "localField": "task_id",
                        "foreignField": "id",
                        "as": "task",
                    }
                },
                {"$unwind": "$task"},
                {
                    "$addFields": {
                        "flag": "$value",
                        "output": "$task.output",
                        "input": "$task.input",
                    }
                },
                {"$project": {"input": 1, "output": 1, "flag": 1}},
            ]
        )
        .to_list(length=None)
    )
    logger.debug(f"Nb of successful examples: {len(successful_examples_tasks)}")

    # Get the failure examples
    unsuccessful_examples_tasks = (
        await mongo_db["evals"]
        .aggregate(
            [
                {
                    "$match": {
                        "project_id": task.project_id,
                        "source": {"$nin": PHOSPHO_EVAL_MODELS_NAMES},
                        "value": "failure",
                    }
                },
                {"$sort": {"created_at": -1}},
                {"$limit": nb_failure},
                {
                    "$lookup": {
                        "from": "tasks",
                        "localField": "task_id",
                        "foreignField": "id",
                        "as": "task",
                    }
                },
                {"$unwind": "$task"},
                {
                    "$addFields": {
                        "flag": "$value",
                        "output": "$task.output",
                        "input": "$task.input",
                    }
                },
                {"$project": {"input": 1, "output": 1, "flag": 1}},
            ]
        )
        .to_list(length=None)
    )
    logger.debug(f"Nb of failure examples: {len(unsuccessful_examples_tasks)}")

    # Get the Task's system prompt
    if task.metadata is not None:
        system_prompt = task.metadata.get("system_prompt", None)
    else:
        system_prompt = None

    # Call the eval function
    # Create the phospho workload
    workload = lab.Workload()
    workload.add_job(
        lab.Job(
            id="evaluate_task",
            job_function=lab.job_library.evaluate_task,
        )
    )
    # Convert to a list of messages
    message = lab.Message.from_task(
        task=task,
        metadata={
            "successful_examples": successful_examples_tasks,
            "unsuccessful_examples": unsuccessful_examples_tasks,
            "system_prompt": system_prompt,
        },
    )
    await workload.async_run(messages=[message], executor_type="sequential")
    # Check the results of the workload
    if workload.results is None:
        logger.error("Worlkload.results is None")
        return None

    job_result = workload.results.get(message.id, {}).get("evaluate_task", None)
    if job_result is None:
        logger.error("Job result in workload is None")
        return None

    flag = job_result.value
    llm_call = job_result.metadata.get("llm_call", None)
    if llm_call is not None:
        llm_call_obj = LlmCall(
            **llm_call, org_id=task.org_id, task_id=task.id, job_id="evaluate_task"
        )
        mongo_db["llm_calls"].insert_one(llm_call_obj.model_dump())

    logger.debug(f"Flag for task {task.id} : {flag}")
    # Create the Evaluation object and store it in the db
    evaluation_data = Eval(
        project_id=task.project_id,
        session_id=task.session_id,
        task_id=task.id,
        value=flag,
        source=config.EVALUATION_SOURCE,
        test_id=task.test_id,
        org_id=task.org_id,
        task=task if not save_task else None,
    )
    mongo_db["evals"].insert_one(evaluation_data.model_dump())

    # Save the prediction
    prediction = await create_prediction(
        task.org_id,
        task.project_id,
        config.TASK_EVALUATION_JOB_ID,
        flag,
        "evaluation",
        task_id=task.id,
    )

    # Update the task object if the flag is None (no previous evaluation)
    if save_task:
        task_in_db = await mongo_db["tasks"].find_one({"id": task.id})
        if task_in_db.get("flag") is None:
            mongo_db["tasks"].update_one(
                {"id": task.id},
                {
                    "$set": {
                        "flag": flag,
                        "last_eval": evaluation_data.model_dump(),
                        "evaluation_source": config.EVALUATION_SOURCE,
                    }
                },
            )
    return flag


# async def topic_extraction_pipeline(task_id: str) -> None:
#     mongo_db = await get_mongo_db()

#     task_data = await mongo_db["tasks"].find_one({"id": task_id})

#     task_input = task_data.get("input", None)
#     task_output = task_data.get("output", None)

#     # Build the text to extract topics from
#     text_input = f"{task_input} {task_output}"

#     detected_topics = extract_topics(text_input)

#     if len(detected_topics) == 0:
#         logger.debug(f"No topics detected for task {task_id}")
#         # Stop the execution of the pipeline
#         return

#     logger.debug(f"Detected topics for task {task_id} : {detected_topics}")

#     # Save the detected topics in the MongoDB document
#     update_result = await mongo_db["tasks"].update_one(
#         {"id": task_id}, {"$set": {"topics": detected_topics}}
#     )

#     # Check if the operation matched and modified any document
#     if update_result.matched_count == 0:
#         raise ValueError(f"Task with id {task_id} not found in the database.")

#     elif update_result.modified_count == 0:
#         logger.warning(
#             "Document found, but no changes were made (it might already have the same topics data)."
#         )

#     else:
#         # The document was not changed in the DB
#         logger.info(f"Detected topics for task {task_id} saved in the database")


async def task_main_pipeline(task: Task, save_task: bool = True) -> PipelineResults:
    """
    Main pipeline to run on a task.
    - Event detection
    - Evaluate task success/failure
    """

    # Get the starting time of the pipeline
    start_time = time.time()
    logger.info(f"Starting main pipeline for task {task.id}")

    # For now, do things sequentially

    # Do the event detection
    if task.test_id is None:
        events = await task_event_detection_pipeline(task, save_task=save_task)

    # Do the session scoring -> success, failure
    mongo_db = await get_mongo_db()
    if save_task:
        task_in_db = await mongo_db["tasks"].find_one({"id": task.id})
        if task_in_db.get("flag") is None:
            flag = await task_scoring_pipeline(task, save_task=save_task)
        else:
            flag = task_in_db.get("flag")
    else:
        flag = await task_scoring_pipeline(task, save_task=save_task)

    # Optional: later add the moderation pipeline on input and outputs

    # Do the topic extraction
    # await topic_extraction_pipeline(task_id)

    # Log the completion of the pipeline and the time it took
    logger.info(
        f"Main pipeline completed in {time.time() - start_time:.2f} seconds for task {task.id}"
    )

    return PipelineResults(
        events=events,
        flag=flag,
    )


async def messages_main_pipeline(
    project_id: str, messages: List[lab.Message]
) -> PipelineResults:
    """
    Main pipeline to run on a list of messages.
    We expect the messages to be in chronological order.
    Only the last message will be used for the event detection.
    The previous messages will be used as context.

    - Event detection
    """
    project = await get_project_by_id(project_id)
    if project.settings is None:
        logger.warning(f"Project with id {project_id} has no settings")
        return []
    workload = lab.Workload.from_phospho_project_config(project)
    message = lab.Message(
        id="single_message",
        role=messages[-1].role,
        content=messages[-1].content,
        metadata=messages[-1].metadata,
        previous_messages=messages[:-1],
    )
    await workload.async_run(messages=[message], executor_type="parallel_jobs")
    events: List[Event] = []
    for event_name, result in workload.results["single_message"].items():
        # We actually ran the pipeline on a single message, with
        # the previous messages as context
        logger.debug(f"Result for {event_name}: {result.value}")
        if result.value is True:
            metadata = workload.jobs[result.job_id].metadata
            event = EventDefinition(**metadata)
            detected_event_data = Event(
                event_name=event_name,
                project_id=project_id,
                source=result.metadata.get("source", "phospho-unknown"),
                webhook=event.webhook,
                event_definition=event,
                messages=messages,
            )
            events.append(detected_event_data)

            if event.webhook is not None:
                await trigger_webhook(
                    url=event.webhook,
                    json=detected_event_data.model_dump(),
                    headers=event.webhook_headers,
                )

        # Save the prediction
        # Get the event object from the settings
        event_settings = project.settings.events.get(event_name)

        # Get the job_id from the event
        job_id = event_settings.job_id

        if job_id is None:
            logger.error(f"No job_id found for event {event_name}")

        else:
            # WARNING: task_id is not available in this context
            prediction = await create_prediction(
                project.org_id, project_id, job_id, result.value, "event_detection"
            )
    # Push the events to the database
    if len(events) > 0:
        mongo_db = await get_mongo_db()
        mongo_db["events"].insert_many([event.model_dump() for event in events])

    return PipelineResults(
        events=events,
        flag=None,
    )
