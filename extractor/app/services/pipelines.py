import time
from typing import Dict

from loguru import logger

from app.core import config
from app.db.models import Eval, Event, EventDefinition, LlmCall, Task
from app.db.mongo import get_mongo_db
from app.services.data import fetch_previous_tasks
from app.services.projects import get_project_by_id

# from app.services.topics import extract_topics  # TODO
from app.services.webhook import trigger_webhook
from phospho import lab


class EventConfig(lab.JobConfig):
    event_name: str
    event_description: str


async def event_detection_pipeline(task: Task) -> None:
    """
    Run the event detection pipeline for a given task
    """
    logger.info(f"Run the event detection pipeline for task {task.id}")
    mongo_db = await get_mongo_db()

    # Get the data of all the task before the task[task_id]
    previous_tasks = await fetch_previous_tasks(task.id)
    task_data = previous_tasks[-1]
    task_context = previous_tasks[:-1]
    # Crop the task context to the last 2 tasks
    if len(task_context) > 2:
        task_context = task_context[-2:]

    # Get the project settings
    project_id = task_data.project_id
    project = await get_project_by_id(project_id)
    logger.debug(f"project_settings {project.settings}")
    if project.settings is None:
        logger.warning(f"Project with id {project_id} has no settings")
        return
    if project.settings.get("events", None) is None:
        logger.warning(f"Project with id {project_id} has no events")
        return

    project_events: Dict[str, dict] = project.settings["events"]
    # Validate the events
    valid_project_events = {}
    for k, v in project_events.items():
        try:
            event_name = v.get("event_name")
            if event_name is None:
                event_name = k
            v["event_name"] = event_name
            valid_project_events[k] = EventDefinition.model_validate(v)
        except Exception as e:
            logger.error(f"Event {k} in project {project_id} is not valid: {e}")

    # Create the phospho workload
    workload = lab.Workload()
    # Add the event detection jobs to the workload
    for event_name, event in valid_project_events.items():
        logger.debug(f"Add event detection job for event {event_name}")
        workload.add_job(
            lab.Job(
                id=event_name,
                job_function=lab.job_library.event_detection,
                config=EventConfig(
                    event_name=event_name,
                    event_description=event.description,
                ),
            )
        )
    # Convert the tasks into a list of messages
    previous_messages = []
    for i, previous_task in enumerate(task_context):
        previous_messages.append(
            lab.Message(
                id="input_" + previous_task.id,
                role="User",
                content=previous_task.input,
            )
        )
        if previous_task.output is not None:
            previous_messages.append(
                lab.Message(
                    id="output_" + previous_task.id,
                    role="Assistant",
                    content=previous_task.output,
                )
            )
    if task_data.output is not None:
        previous_messages.append(
            lab.Message(
                id="input_" + task_data.id,
                role="User",
                content=task_data.input,
            )
        )
        latest_message_id = "output_" + task_data.id
        await workload.async_run(
            messages=[
                lab.Message(
                    id=latest_message_id,
                    content=task_data.output,
                    previous_messages=previous_messages,
                )
            ],
            executor_type="sequential",
        )
    else:
        latest_message_id = "input_" + task_data.id
        await workload.async_run(
            messages=[
                lab.Message(
                    id=latest_message_id,
                    role="User",
                    content=task_data.input,
                    previous_messages=previous_messages,
                )
            ],
            executor_type="sequential",
        )

    # Check the results of the workload
    message_results = workload.results[latest_message_id]
    logger.debug(f"Results of the event detection pipeline: {message_results}")
    for event_name, result in message_results.items():
        # Store the LLM call in the database
        metadata = result.metadata
        llm_call = metadata.get("llm_call", None)
        if llm_call is not None:
            llm_call_obj = LlmCall(
                **llm_call,
                org_id=task_data.org_id,
                task_id=task.id,
                job_id="event_name",
            )
            mongo_db["llm_calls"].insert_one(llm_call_obj.model_dump())

        # When the event is detected, result is True
        if result.value:
            logger.info(f"Event {event_name} detected for task {task_data.id}")
            # Get the event definition
            event = valid_project_events[event_name]
            # Push to db
            detected_event_data = Event(
                event_name=event_name,
                task_id=task_data.id,
                session_id=task_data.session_id,
                project_id=project_id,
                source=result.metadata.get("source", "phospho-unknown"),
                webhook=event.webhook,
                org_id=task_data.org_id,
            )
            mongo_db["events"].insert_one(detected_event_data.model_dump())
            # Update the task object with the event
            mongo_db["tasks"].update_one(
                {"id": task.id},
                # Add the event to the list of events
                {"$push": {"events": detected_event_data.model_dump()}},
            )
            # Trigger the webhook if it exists
            if event.webhook is not None:
                trigger_webhook(
                    url=event.webhook,
                    json=detected_event_data.model_dump(),
                    headers=event.webhook_headers,
                )


async def task_scoring_pipeline(task: Task) -> None:
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
    if task.output is not None:
        messages = [
            lab.Message(
                id="output_" + task.id,
                role="Assistant",
                content=task.output,
                previous_messages=[
                    lab.Message(
                        id="input_" + task.id,
                        role="User",
                        content=task.input,
                    )
                ],
                metadata={
                    "successful_examples": successful_examples_tasks,
                    "unsuccessful_examples": unsuccessful_examples_tasks,
                },
            )
        ]
    else:
        messages = [
            lab.Message(
                id="input_" + task.id,
                role="User",
                content=task.input,
                metadata={
                    "successful_examples": successful_examples_tasks,
                    "unsuccessful_examples": unsuccessful_examples_tasks,
                },
            )
        ]
    await workload.async_run(messages=messages, executor_type="sequential")
    # Check the results of the workload
    flag = workload.results["output_" + task.id]["evaluate_task"].value
    metadata = workload.results["output_" + task.id]["evaluate_task"].metadata
    llm_call = metadata.get("llm_call", None)
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
    )
    mongo_db["evals"].insert_one(evaluation_data.model_dump())

    # Update the task object
    mongo_db["tasks"].update_one(
        {"id": task.id},
        {"$set": {"flag": flag, "last_eval": evaluation_data.model_dump()}},
    )


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


async def main_pipeline(task: Task) -> None:
    """
    Main interface with the watcher service
    TODO : a call to the pipeline create a Prediction object in the database to keep track of the pipeline activity
    """

    # Get the starting time of the pipeline
    start_time = time.time()
    logger.info(f"Starting main pipeline for task {task.id}")

    # For now, do things sequentially

    # Do the event detection
    if task.test_id is None:
        await event_detection_pipeline(task)

    # Do the session scoring -> success, failure
    if task.flag is None:
        mongo_db = await get_mongo_db()

        await task_scoring_pipeline(task)
        # Optional: later add the moderation pipeline on input and outputs

        # Update the task with the prediction source that was used
        await mongo_db["tasks"].update_one(
            {"id": task.id}, {"$set": {"evaluation_source": config.EVALUATION_SOURCE}}
        )

    # Do the topic extraction
    # await topic_extraction_pipeline(task_id)

    # Log the completion of the pipeline and the time it took
    logger.info(
        f"Main pipeline completed in {time.time() - start_time:.2f} seconds for task {task.id}"
    )
