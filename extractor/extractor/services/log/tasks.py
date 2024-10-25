from typing import List, Dict, Any, Literal, Tuple, Optional
from extractor.models.log import MinimalLogEventForMessages
from extractor.models.pipelines import RoleContentMessage
from extractor.services.pipelines import MainPipeline
from extractor.models import LogEventForTasks
from phospho.models import Task, Session
from extractor.services.log.base import (
    convert_additional_data_to_dict,
    get_time_created_at,
    collect_metadata,
)
from loguru import logger
from extractor.db.mongo import get_mongo_db
from extractor.services.tasks import compute_task_position
from extractor.utils import generate_uuid


async def process_tasks_id(
    project_id: str,
    org_id: str,
    tasks_id_to_process: List[str],
) -> None:
    """
    From tasks id, process the tasks
    - Trigger the Tasks processing pipeline
    """

    main_pipeline = MainPipeline(
        project_id=project_id,
        org_id=org_id,
    )

    await main_pipeline.set_input(tasks_ids=tasks_id_to_process)

    await main_pipeline.run()

    return None


def create_task_from_logevent(
    org_id: str,
    project_id: str,
    log_event: LogEventForTasks,
    session_id: Optional[str] = None,
    log_event_metadata: Optional[Dict[str, Any]] = None,
) -> Task:
    if log_event_metadata is None:
        log_event_metadata = {}

    if log_event.project_id is None:
        log_event.project_id = project_id
    task = Task(
        id=log_event.task_id,
        project_id=log_event.project_id,
        org_id=org_id,
        created_at=get_time_created_at(
            log_event.client_created_at, log_event.created_at
        ),
        session_id=session_id,
        input=log_event.input,
        additional_input=convert_additional_data_to_dict(
            log_event.raw_input, "raw_input"
        ),
        output=log_event.output,
        additional_output=convert_additional_data_to_dict(
            log_event.raw_output, "raw_output"
        ),
        metadata=log_event_metadata,
        data=None,
        flag=log_event.flag,
        test_id=log_event.test_id,
    )
    return task


async def ignore_existing_tasks(
    tasks_to_create: List[Dict[str, object]],
    tasks_id_to_process: List[str],
) -> Tuple[List[Dict[str, object]], List[str]]:
    """
    Filter out tasks that already exist in the database
    """
    mongo_db = await get_mongo_db()
    existing_tasks = (
        await mongo_db["tasks"]
        .find({"id": {"$in": [task["id"] for task in tasks_to_create]}})
        .to_list(length=len(tasks_to_create))
    )
    existing_task_ids = [task["id"] for task in existing_tasks]
    new_tasks_to_create = []
    for task in tasks_to_create:
        if (
            task["id"] not in existing_task_ids
            and task["id"] not in new_tasks_to_create
        ):
            new_tasks_to_create.append(task)

    # Filter tasks_id_to_process
    tasks_id_to_process = [
        task_id for task_id in tasks_id_to_process if task_id not in existing_task_ids
    ]

    return new_tasks_to_create, tasks_id_to_process


async def process_log_without_session_id(
    project_id: str,
    org_id: str,
    list_of_log_event: List[LogEventForTasks],
    trigger_pipeline: bool = True,
    batch_size: Optional[int] = 256,
) -> None:
    """
    Process a list of log events without session_id
    """
    if len(list_of_log_event) == 0:
        logger.debug("No log event without session_id to process")
        return None
    logger.info(
        f"Project {project_id}: processing {len(list_of_log_event)} log events without session_id"
    )
    mongo_db = await get_mongo_db()

    tasks_id_to_process: List[str] = []
    tasks_to_create: List[Dict[str, object]] = []
    for log_event in list_of_log_event:
        log_event_metadata = collect_metadata(log_event)
        # Generate a default session_id
        task = create_task_from_logevent(
            org_id=org_id,
            project_id=project_id,
            log_event=log_event,
            session_id=None,
            log_event_metadata=log_event_metadata,
        )
        tasks_id_to_process.append(task.id)
        tasks_to_create.append(task.model_dump())

    # Skip task creation if there is no task to create
    if len(tasks_to_create) == 0:
        logger.debug("No task to create")
        return None

    # Create the tasks
    tasks_to_create, tasks_id_to_process = await ignore_existing_tasks(
        tasks_to_create, tasks_id_to_process
    )
    if len(tasks_to_create) > 0:
        try:
            await mongo_db["tasks"].insert_many(tasks_to_create, ordered=False)
        except Exception as e:
            error_mesagge = f"Error saving tasks to the database: {e}"
            logger.error(error_mesagge)

    if trigger_pipeline:
        logger.info(f"Triggering pipeline for {len(tasks_id_to_process)} tasks")
        # Vectorize them
        # await add_vectorized_tasks(tasks_id_to_process)
        main_pipeline = MainPipeline(
            project_id=project_id,
            org_id=org_id,
        )
        # Batch the processing
        if batch_size is not None:
            for i in range(0, len(tasks_id_to_process), batch_size):
                await main_pipeline.set_input(
                    tasks_ids=tasks_id_to_process[i : i + batch_size]
                )
                await main_pipeline.run()
        else:
            await main_pipeline.set_input(tasks_ids=tasks_id_to_process)
            await main_pipeline.run()

    return None


async def process_log_with_session_id(
    project_id: str,
    org_id: str,
    list_of_log_event: List[LogEventForTasks],
    trigger_pipeline: bool = True,
    batch_size: Optional[int] = 256,
) -> None:
    """
    Process a list of log events with session_id
    """
    if len(list_of_log_event) == 0:
        logger.debug("No log event with session_id to process")
        return None

    logger.info(
        f"Project {project_id}: processing {len(list_of_log_event)} log events with session_id"
    )
    tasks_id_to_process: List[str] = []
    tasks_to_create: List[Dict[str, object]] = []
    sessions_to_create: Dict[str, Dict[str, Any]] = {}
    sessions_to_earliest_task: Dict[str, Task] = {}

    mongo_db = await get_mongo_db()
    sessions_ids_already_in_db = (
        await mongo_db["sessions"]
        .aggregate(
            [
                {
                    "$match": {
                        "id": {
                            "$in": [
                                log_event.session_id for log_event in list_of_log_event
                            ]
                        }
                    }
                },
                {"$project": {"id": 1}},
            ]
        )
        .to_list(length=len(list_of_log_event))
    )
    sessions_ids_already_in_db = [
        str(session["id"]) for session in sessions_ids_already_in_db
    ]

    for log_event in list_of_log_event:
        if log_event.project_id is None:
            log_event.project_id = project_id

        # Calculate log_event metadata
        log_event_metadata = collect_metadata(log_event)

        # Only create a new session if the session doesn't exist in db
        session_is_in_db = log_event.session_id in sessions_ids_already_in_db

        session_project_id = project_id
        if log_event.project_id is not None:
            session_project_id = log_event.project_id

        if (
            log_event.session_id is not None
            and not session_is_in_db
            and log_event.session_id not in sessions_to_create.keys()
        ):
            # Add to sessions to create
            session_data: Dict[str, Any] = {
                "id": log_event.session_id,
                "project_id": session_project_id,
                # Note: there is no metadata and data
                "metadata": {
                    "total_tokens": log_event_metadata.get("total_tokens", 0),
                    "prompt_tokens": log_event_metadata.get("prompt_tokens", 0),
                    "completion_tokens": log_event_metadata.get("completion_tokens", 0),
                },
                "data": {},
                "session_length": 1,
            }
            # The sessions will be created later, once we know the earliest task creation time
            sessions_to_create[log_event.session_id] = session_data
        elif (
            log_event.session_id is not None
            and log_event.session_id in sessions_to_create.keys()
        ):
            # Increment the session length of the session to create
            sessions_to_create[log_event.session_id]["session_length"] += 1
        elif log_event.session_id is not None and session_is_in_db:
            # Increment the session length, total_tokens, prompt_tokens and completion_tokens in the database
            mongo_db["sessions"].update_one(
                {"id": log_event.session_id},
                {
                    "$inc": {
                        "session_length": 1,
                        "metadata.total_tokens": log_event_metadata.get("total_tokens")
                        or 0,
                        "metadata.prompt_tokens": log_event_metadata.get(
                            "prompt_tokens"
                        )
                        or 0,
                        "metadata.completion_tokens": log_event_metadata.get(
                            "completion_tokens"
                        )
                        or 0,
                    }
                },
            )
        else:
            logger.info(
                "Log event: session with no session_id, skipping session creation"
            )

        task = create_task_from_logevent(
            org_id=org_id,
            project_id=log_event.project_id,
            log_event=log_event,
            session_id=log_event.session_id,
            log_event_metadata=log_event_metadata,
        )
        tasks_id_to_process.append(task.id)
        tasks_to_create.append(task.model_dump())

        # Update the session creation time if needed
        if log_event.session_id is not None:
            if log_event.session_id not in sessions_to_earliest_task.keys():
                sessions_to_earliest_task[log_event.session_id] = task
            else:
                # Update it if lower
                if (
                    task.created_at
                    < sessions_to_earliest_task[log_event.session_id].created_at
                ):
                    sessions_to_earliest_task[log_event.session_id] = task

    # Create the tasks
    tasks_to_create, tasks_id_to_process = await ignore_existing_tasks(
        tasks_to_create, tasks_id_to_process
    )
    if len(tasks_to_create) > 0:
        try:
            await mongo_db["tasks"].insert_many(tasks_to_create, ordered=False)
        except Exception as e:
            error_mesagge = f"Error saving tasks to the database: {e}"
            logger.error(error_mesagge)

    # Add sessions to database
    if len(sessions_to_create) > 0 and len(tasks_to_create) > 0:
        sessions_to_create_dump: List[dict] = []
        for session_id, session_data in sessions_to_create.items():
            # logger.info(
            #     f"Logevent: creating session with session_id {session_id} from log event"
            # )
            # Verify if the session already exists
            session_is_in_db = session_id in sessions_ids_already_in_db
            if session_is_in_db:
                # Increment the session length in the database
                await mongo_db["sessions"].update_one(
                    {"id": session_id},
                    {
                        "$inc": {"session_length": session_data["session_length"]},
                    },
                )
            else:
                session = Session(
                    id=session_id,
                    created_at=sessions_to_earliest_task[session_id].created_at,
                    project_id=session_data["project_id"],
                    org_id=org_id,
                    metadata=session_data["metadata"],
                    data=session_data["data"],
                    preview=sessions_to_earliest_task[session_id].preview(),
                    session_length=session_data["session_length"],
                )
                sessions_to_create_dump.append(session.model_dump())

        if len(sessions_to_create_dump) > 0:
            logger.info(
                f"Creating sessions: {' '.join([session_id for session_id in sessions_to_create.keys()])}"
            )
            try:
                insert_result = await mongo_db["sessions"].insert_many(
                    sessions_to_create_dump, ordered=False
                )
                logger.info(f"Created {len(insert_result.inserted_ids)} sessions")
            except Exception as e:
                error_mesagge = f"Error saving sessions to the database: {e}"
                logger.error(error_mesagge)
    else:
        logger.info("Logevent: no session to create")

    # Compute the task position
    await compute_task_position(
        project_id=project_id,
        session_ids=list(sessions_to_create.keys()) + sessions_ids_already_in_db,
    )

    if trigger_pipeline:
        logger.info(f"Triggering pipeline for {len(tasks_id_to_process)} tasks")
        # await add_vectorized_tasks(tasks_id_to_process)
        main_pipeline = MainPipeline(
            project_id=project_id,
            org_id=org_id,
        )
        # Batch the processing
        if batch_size is not None:
            for i in range(0, len(tasks_id_to_process), batch_size):
                await main_pipeline.set_input(
                    tasks_ids=tasks_id_to_process[i : i + batch_size]
                )
                await main_pipeline.run()
        else:
            await main_pipeline.set_input(tasks_ids=tasks_id_to_process)
            await main_pipeline.run()


async def process_logs_for_tasks(
    project_id: str,
    org_id: str,
    logs_to_process: List[LogEventForTasks],
    extra_logs_to_save: List[LogEventForTasks],
) -> None:
    """From logs
    - Create Tasks
    - Create a Session
    - Trigger the Tasks processing pipeline
    """
    mongo_db = await get_mongo_db()
    logger.info(f"Project {project_id}: processing {len(logs_to_process)} log events")

    def log_is_error(log_event):
        if isinstance(log_event, dict) and "Error in log" in log_event:
            return True
        return False

    nonerror_log_events = []
    error_log_events = []
    for log_event in logs_to_process + extra_logs_to_save:
        if not log_is_error(log_event) and isinstance(log_event, LogEventForTasks):
            nonerror_log_events.append(log_event)
        else:
            error_log_events.append(log_event)

    logger.info(
        f"Project {project_id}: saving {len(nonerror_log_events)} non-error log events"
    )
    # Save the non-error log events
    if len(nonerror_log_events) > 0:
        try:
            mongo_db["logs"].insert_many(
                [log_event.model_dump() for log_event in nonerror_log_events]
            )
        except Exception as e:
            error_mesagge = f"Error saving logs to the database: {e}"
            logger.error(error_mesagge)
    # Save the error log events
    if len(error_log_events) > 0:
        logger.error(
            f"Project {project_id}: saving {len(error_log_events)} error log events"
        )
        try:
            mongo_db["log_errors"].insert_many(
                [log_event.model_dump() for log_event in error_log_events]
            )
        except Exception as e:
            error_mesagge = f"Error saving logs to the database: {e}"
            logger.error(error_mesagge)

    # For logs without session_id, we generate a new session_id
    for log_event in logs_to_process:
        if log_event.session_id is None:
            log_event.session_id = "session_" + generate_uuid()

    # Process logs with session_id
    await process_log_with_session_id(
        project_id=project_id,
        org_id=org_id,
        list_of_log_event=[
            log_event
            for log_event in logs_to_process
            if log_event.session_id is not None
        ],
    )

    if len(extra_logs_to_save) > 0:
        logger.info(
            f"Project {project_id}: saving {len(extra_logs_to_save)} extra log events"
        )
        for log_event in extra_logs_to_save:
            if log_event.session_id is None:
                log_event.session_id = "session_" + generate_uuid()

        # Process logs with session_id
        await process_log_with_session_id(
            project_id=project_id,
            org_id=org_id,
            list_of_log_event=[
                log_event
                for log_event in extra_logs_to_save
                if log_event.session_id is not None
            ],
            trigger_pipeline=False,
        )

    return None


async def process_logs_for_messages(
    project_id: str,
    org_id: str,
    logs_to_process: List[MinimalLogEventForMessages],
    extra_logs_to_save: List[MinimalLogEventForMessages],
) -> None:
    """
    Convert MinimalLogEventForMessages to LogEventForTasks and process them using process_logs_for_tasks
    """

    logs_to_process_for_tasks = []
    extra_logs_to_save_for_tasks = []

    for log_event in logs_to_process:
        messages = log_event.messages

        if messages[0].role == "system":
            metadata = {
                **(log_event.metadata or {}),
                "system_prompt": messages[0].content,
            }

            logs_events_for_tasks = await convert_messages_to_tasks(
                project_id=project_id,
                session_id=log_event.session_id,
                messages=messages[1:],
                merge_mode=log_event.merge_mode,
                created_at=log_event.created_at,
                metadata=metadata,
                version_id=log_event.version_id,
                user_id=log_event.user_id,
                flag=log_event.flag,
                test_id=log_event.test_id,
            )

        else:
            logs_events_for_tasks = await convert_messages_to_tasks(
                project_id=project_id,
                session_id=log_event.session_id,
                messages=messages,
                merge_mode=log_event.merge_mode,
                created_at=log_event.created_at,
                metadata=log_event.metadata,
                version_id=log_event.version_id,
                user_id=log_event.user_id,
                flag=log_event.flag,
                test_id=log_event.test_id,
            )
        logs_to_process_for_tasks.extend(logs_events_for_tasks)

    for log_event in extra_logs_to_save:
        messages = log_event.messages

        if messages[0].role == "system":
            metadata = {
                **(log_event.metadata or {}),
                "system_prompt": messages[0].content,
            }
            logs_events_for_tasks = await convert_messages_to_tasks(
                project_id=project_id,
                session_id=log_event.session_id,
                messages=messages[1:],
                merge_mode=log_event.merge_mode,
                created_at=log_event.created_at,
                metadata=metadata,
                version_id=log_event.version_id,
                user_id=log_event.user_id,
                flag=log_event.flag,
                test_id=log_event.test_id,
            )

        else:
            logs_events_for_tasks = await convert_messages_to_tasks(
                project_id=project_id,
                session_id=log_event.session_id,
                messages=messages,
                merge_mode=log_event.merge_mode,
                created_at=log_event.created_at,
                metadata=log_event.metadata,
                version_id=log_event.version_id,
                user_id=log_event.user_id,
                flag=log_event.flag,
                test_id=log_event.test_id,
            )
        extra_logs_to_save_for_tasks.extend(logs_events_for_tasks)

    await process_logs_for_tasks(
        project_id=project_id,
        org_id=org_id,
        logs_to_process=logs_to_process_for_tasks,
        extra_logs_to_save=extra_logs_to_save_for_tasks,
    )

    return None


async def convert_messages_to_tasks(
    project_id: str,
    session_id: str,
    messages: List[RoleContentMessage],
    merge_mode: Literal["resolve", "append", "replace"] = "resolve",
    metadata: Optional[Dict[str, Any]] = None,
    version_id: Optional[str] = None,
    created_at: Optional[int] = None,
    user_id: Optional[str] = None,
    flag: Optional[Literal["success", "failure"]] = None,
    test_id: Optional[str] = None,
) -> List[LogEventForTasks]:
    """
    Convert messages to LogEventForTasks
    """
    log_events = []
    for i, message in enumerate(messages):
        if i % 2 == 0:
            input_message = message.content
        if i % 2 == 1:
            output_message = message.content
            log_event = LogEventForTasks(
                project_id=project_id,
                input=input_message,
                output=output_message,
                session_id=session_id,
                created_at=created_at,
                metadata=metadata,
                version_id=version_id,
                user_id=user_id,
                flag=flag,
                test_id=test_id,
            )
            log_events.append(log_event)
    if len(messages) % 2 == 1:
        log_event = LogEventForTasks(
            project_id=project_id,
            input=messages[-1].content,
            output=None,
            session_id=session_id,
            created_at=created_at,
            metadata=metadata,
            version_id=version_id,
            user_id=user_id,
            flag=flag,
            test_id=test_id,
        )
        log_events.append(log_event)
    return log_events
