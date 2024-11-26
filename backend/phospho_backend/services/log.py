from typing import Any, Dict, List, Optional, Tuple, Union

from phospho_backend.api.v2.models import LogEvent
from phospho_backend.db.mongo import get_mongo_db
from phospho_backend.services.mongo.extractor import ExtractorClient
from phospho_backend.services.mongo.projects import (
    project_check_automatic_analytics_monthly_limit,
)
from phospho_backend.utils import generate_timestamp, generate_uuid
from loguru import logger

from phospho.lab.utils import get_tokenizer, num_tokens_from_messages
from phospho.models import HumanEval, Session, Task
from phospho.utils import filter_nonjsonable_keys, is_jsonable


async def create_task_and_process_logs(
    logs_to_process: List[LogEvent],
    extra_logs_to_save: List[LogEvent],
    project_id: str,
    org_id: str,
):
    mongo_db = await get_mongo_db()

    def log_is_error(log_event):
        if isinstance(log_event, dict) and "Error in log" in log_event:
            return True
        return False

    nonerror_log_events = []
    error_log_events = []
    for log_event in logs_to_process + extra_logs_to_save:
        if not log_is_error(log_event) and isinstance(log_event, LogEvent):
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


async def process_log_with_session_id(
    project_id: str,
    org_id: str,
    list_of_log_event: List[LogEvent],
    trigger_pipeline: bool = True,
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
            logger.info(f"Creating {len(sessions_to_create_dump)} 'sessions")
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

    logger.info(f"Triggering pipeline for {len(tasks_id_to_process)} tasks")

    run_analytics = (
        not await project_check_automatic_analytics_monthly_limit(project_id)
    ) and trigger_pipeline

    extractor_client = ExtractorClient(
        project_id=project_id,
        org_id=org_id,
    )
    await extractor_client.run_process_tasks(
        tasks_id_to_process=tasks_id_to_process,
        run_analytics=run_analytics,
    )


def collect_metadata(log_event: LogEvent) -> dict:
    """
    Collect the metadata from the log event.
    - Add all unknown fields to the metadata
    - Filter non-jsonable values
    - Compute token count if not present
    """
    # Collect the metadata
    metadata = getattr(log_event, "metadata", {})
    if metadata is None:
        metadata = {}

    # Add all unknown fields to the metadata
    for key, value in log_event.model_dump().items():
        if (
            key not in metadata.keys()
            and key not in Task.model_fields.keys()
            and key not in ["raw_input", "raw_output"]
            and is_jsonable(value)
        ):
            metadata[key] = value
    # Filter non-jsonable values
    metadata = filter_nonjsonable_keys(metadata)

    # Compute token count
    model = metadata.get("model", None)
    if not isinstance(model, str):
        model = None

    if "prompt_tokens" not in metadata.keys():
        metadata["prompt_tokens"] = get_nb_tokens_prompt_tokens(log_event, model)

    if "completion_tokens" not in metadata.keys():
        metadata["completion_tokens"] = get_nb_tokens_completion_tokens(
            log_event, model
        )

    if "total_tokens" not in metadata.keys():
        # If prompt_tokens or completion_tokens are None, set total_tokens to None
        # This is the case when someone specifically sets prompt_tokens or completion_tokens to None
        if (
            metadata.get("prompt_tokens", 0) is None
            or metadata.get("completion_tokens", 0) is None
        ):
            metadata["total_tokens"] = None
        else:
            prompt_tokens = metadata.get("prompt_tokens", 0)
            completion_tokens = metadata.get("completion_tokens", 0)
            if not isinstance(prompt_tokens, int):
                prompt_tokens = 0
            if not isinstance(completion_tokens, int):
                completion_tokens = 0
            metadata["total_tokens"] = prompt_tokens + completion_tokens

    return metadata


def convert_additional_data_to_dict(
    data: Union[dict, str, list, None],
    default_key_name: str,
) -> Optional[dict]:
    """This conversion function is used so that the additional_input and additional_output are always a dict."""
    if isinstance(data, dict):
        # If it's already a dict, just return it
        return data
    elif isinstance(data, str):
        # If it's a string, return a dict with the default key name
        return {default_key_name: data}
    elif isinstance(data, list):
        # If it's a list, return a dict with the default key name
        return {default_key_name: data}
    else:
        # Otherwise, it's unsuported. Return None
        return None


def get_time_created_at(
    client_created_at: Optional[int], created_at: Optional[int]
) -> int:
    """
    By default, the created_at of the task is the one from the client
    The client can send us weird values. Take care of the most obvious ones:
    if negative or more than 24 hours in the future, set to current time
    """
    # If created_at is not None, use it
    if created_at is not None:
        client_created_at = created_at

    if client_created_at is None:
        return generate_timestamp()
    if (client_created_at < 0) or (
        client_created_at > generate_timestamp() + 24 * 60 * 60
    ):
        return generate_timestamp()
    return client_created_at


def get_nb_tokens_prompt_tokens(
    log_event: LogEvent, model: Optional[str]
) -> int | None:
    """
    Returns the number of tokens in the prompt tokens, using
    different heuristics depending on the input type.
    """
    tokenizer = get_tokenizer(model)
    if isinstance(log_event.raw_input, dict):
        # Assume there is a key 'messages' (OpenAI-like input)
        try:
            if isinstance(log_event.raw_output, dict):
                usage = log_event.raw_output.get("usage", {})
                if usage:
                    return usage.get("prompt_tokens", None)  # type: ignore
            else:
                messages = log_event.raw_input.get("messages", [])
                if isinstance(messages, list) and all(
                    isinstance(x, dict) for x in messages
                ):
                    return num_tokens_from_messages(
                        messages,
                        model=model,
                        tokenizer=tokenizer,
                    )
        except Exception as e:
            logger.warning(
                f"Error in get_nb_tokens_prompt_tokens with model: {model}, {e}"
            )
    if isinstance(log_event.raw_input, list):
        if all(isinstance(x, str) for x in log_event.raw_input):
            # Handle the case where the input is a list of strings
            return sum(len(tokenizer.encode(x)) for x in log_event.raw_input)  # type: ignore
        if all(isinstance(x, dict) for x in log_event.raw_input):
            # Assume it's a list of messages
            return num_tokens_from_messages(
                log_event.raw_input,  # type: ignore
                model=model,
                tokenizer=tokenizer,
            )
    # Encode the string input
    return len(tokenizer.encode(log_event.input))


def get_nb_tokens_completion_tokens(
    log_event: LogEvent, model: Optional[str]
) -> int | None:
    """
    Returns the number of tokens in the completion tokens, using
    different heuristics depending on the output type.
    """
    try:
        if isinstance(log_event.raw_output, dict):
            # Assume there is a key 'choices' (OpenAI-like output)
            try:
                usage = log_event.raw_output.get("usage", {})
                logger.debug(f"Usage: {usage}")
                if usage:
                    return usage.get("total_tokens", None)  # type: ignore
                else:
                    generated_choices = log_event.raw_output.get("choices", [])
                    logger.debug(f"Generated choices: {generated_choices}")
                    if isinstance(generated_choices, list) and all(
                        isinstance(x, dict) for x in generated_choices
                    ):
                        generated_messages = [
                            choice.get("message", {}) for choice in generated_choices
                        ]
                        return num_tokens_from_messages(generated_messages, model=model)
            except Exception as e:
                logger.warning(
                    f"Error in get_nb_tokens_completion_tokens with model: {model}, {e}"
                )
                return None
        if isinstance(log_event.raw_output, list):
            raw_output_nonull = [x for x in log_event.raw_output if x is not None]
            # Assume it's a list of str
            if all(isinstance(x, str) for x in raw_output_nonull):
                tokenizer = get_tokenizer(model)
                return sum(len(tokenizer.encode(x)) for x in raw_output_nonull)  # type: ignore
            # If it's a list of dict, assume it's a list of streamed chunks
            if all(isinstance(x, dict) for x in raw_output_nonull):
                return len(log_event.raw_output)
        if log_event.output is not None:
            tokenizer = get_tokenizer(model)
            return len(tokenizer.encode(log_event.output))
    except Exception as e:
        logger.error(
            f"Error in get_nb_tokens_completion_tokens with model: {model}, {e}"
        )

    return None


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


def create_task_from_logevent(
    org_id: str,
    project_id: str,
    log_event: LogEvent,
    session_id: Optional[str] = None,
    log_event_metadata: Optional[Dict[str, Any]] = None,
) -> Task:
    if log_event_metadata is None:
        log_event_metadata = {}

    if log_event.project_id is None:
        log_event.project_id = project_id

    # Create a human eval if flag is set
    if log_event.flag:
        human_eval = HumanEval(
            flag=log_event.flag,
        )
    else:
        human_eval = None

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
        human_eval=human_eval,
    )
    return task


async def compute_task_position(
    project_id: str, session_ids: Optional[list[str]] = None
):
    """
    Executes an aggregation pipeline to compute the task position for each task.
    """
    mongo_db = await get_mongo_db()

    main_filter: Dict[str, object] = {"project_id": project_id}
    if session_ids is not None:
        main_filter["id"] = {"$in": session_ids}

    pipeline = [
        {
            "$match": main_filter,
        },
        {
            "$lookup": {
                "from": "tasks",
                "localField": "id",
                "foreignField": "session_id",
                "as": "tasks",
            }
        },
        {
            "$set": {
                "tasks": {
                    "$sortArray": {
                        "input": "$tasks",
                        "sortBy": {"tasks.created_at": 1},
                    },
                }
            }
        },
        # Transform to get 1 doc = 1 task. We also add the task position.
        {"$unwind": {"path": "$tasks", "includeArrayIndex": "task_position"}},
        # Set "is_last_task" to True for the task where task_position is == session.session_length - 1
        {
            "$set": {
                "tasks.is_last_task": {
                    "$eq": ["$task_position", {"$subtract": ["$session_length", 1]}]
                }
            }
        },
        {
            "$project": {
                "id": "$tasks.id",
                "task_position": {"$add": ["$task_position", 1]},
                "is_last_task": "$tasks.is_last_task",
                "_id": 0,
            }
        },
        {
            "$merge": {
                "into": "tasks",
                "on": "id",
                "whenMatched": "merge",
                "whenNotMatched": "discard",
            }
        },
    ]

    await mongo_db["sessions"].aggregate(pipeline).to_list(length=None)
