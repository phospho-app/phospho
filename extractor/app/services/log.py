from typing import Any, Dict, List, Optional, Union

import openai
import tiktoken
from loguru import logger

# DB
from app.api.v1.models import LogEvent, LogReply
from app.db.models import Session, Task
from app.db.mongo import get_mongo_db
from app.db.qdrant import get_qdrant, models
from app.services.pipelines import main_pipeline

# Service
from app.services.tasks import get_task_by_id
from app.utils import generate_timestamp
from phospho.utils import filter_nonjsonable_keys, is_jsonable


# Create a task
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


def get_time_created_at(client_created_at: Optional[int], created_at: Optional[int]):
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


def get_tokenizer(model: Optional[str]) -> tiktoken.Encoding:
    if model is None:
        logger.debug("Model not found. Using cl100k_base tokenizer.")
        return tiktoken.get_encoding("cl100k_base")
    try:
        return tiktoken.encoding_for_model(model)
    except KeyError:
        logger.warning("Model not found. Using cl100k_base tokenizer.")
        return tiktoken.get_encoding("cl100k_base")


def num_tokens_from_messages(
    messages: List[dict], model: Optional[str] = "gpt-3.5-turbo-0613", tokenizer=None
):
    """
    Return the number of tokens used by a list of messages.

    https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
    """
    if tokenizer is None:
        tokenizer = get_tokenizer(model)
    if model is None:
        logger.warning(
            "num_tokens_from_messages() was called without a model. Using gpt-3.5-turbo"
        )
        model = "gpt-3.5-turbo"
    if model in {
        "gpt-3.5-turbo-0613",
        "gpt-3.5-turbo-16k-0613",
        "gpt-4-0314",
        "gpt-4-32k-0314",
        "gpt-4-0613",
        "gpt-4-32k-0613",
    }:
        tokens_per_message = 3
        tokens_per_name = 1
    elif model == "gpt-3.5-turbo-0301":
        tokens_per_message = (
            4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
        )
        tokens_per_name = -1  # if there's a name, the role is omitted
    elif "gpt-3.5-turbo" in model:
        logger.debug(
            "Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613."
        )
        return num_tokens_from_messages(messages, model="gpt-3.5-turbo-0613")
    elif "gpt-4" in model:
        logger.debug(
            "Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613."
        )
        return num_tokens_from_messages(messages, model="gpt-4-0613")
    else:
        logger.warning(
            f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."""
        )
    num_tokens = 0
    for message in messages:
        num_tokens += tokens_per_message
        for key, value in message.items():
            num_tokens += len(tokenizer.encode(value))
            if key == "name":
                num_tokens += tokens_per_name
    num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
    return num_tokens


def get_nb_tokens_prompt_tokens(
    log_event: LogEvent, model: Optional[str], tokenizer: Any
):
    """
    Returns the number of tokens in the prompt tokens, using
    different heuristics depending on the input type.
    """
    if tokenizer is None:
        tokenizer = get_tokenizer(model)
    if isinstance(log_event.raw_input, dict):
        # Assume there is a key 'messages' (OpenAI-like input)
        messages = log_event.raw_input.get("messages", [])
        if isinstance(messages, list) and all(isinstance(x, dict) for x in messages):
            return num_tokens_from_messages(
                messages,
                model=model,
                tokenizer=tokenizer,
            )
    if isinstance(log_event.raw_input, list):
        if all(isinstance(x, str) for x in log_event.raw_input):
            # Handle the case where the input is a list of strings
            return sum(len(tokenizer.encode(x)) for x in log_event.raw_input)
        if all(isinstance(x, dict) for x in log_event.raw_input):
            # Assume it's a list of messages
            return num_tokens_from_messages(
                log_event.raw_input, model=model, tokenizer=tokenizer
            )
    # Encode the string input
    return len(tokenizer.encode(log_event.input))


def get_nb_tokens_completion_tokens(
    log_event: LogEvent, model: Optional[str], tokenizer: Any
):
    """
    Returns the number of tokens in the completion tokens, using
    different heuristics depending on the output type.
    """
    try:
        if tokenizer is None:
            tokenizer = get_tokenizer(model)
        if isinstance(log_event.raw_output, dict):
            # Assume there is a key 'choices' (OpenAI-like output)
            generated_choices = log_event.raw_output.get("choices", [])
            if isinstance(generated_choices, list) and all(
                isinstance(x, dict) for x in generated_choices
            ):
                generated_messages = [
                    choice.get("message", {}) for choice in generated_choices
                ]
                return num_tokens_from_messages(
                    generated_messages, model=model, tokenizer=tokenizer
                )
        if isinstance(log_event.raw_output, list):
            raw_output_nonull = [x for x in log_event.raw_output if x is not None]
            # Assume it's a list of str
            if all(isinstance(x, str) for x in raw_output_nonull):
                return sum(len(tokenizer.encode(x)) for x in raw_output_nonull)
            # If it's a list of dict, assume it's a list of streamed chunks
            if all(isinstance(x, dict) for x in raw_output_nonull):
                return len(log_event.raw_output)
        if log_event.output is not None:
            return len(tokenizer.encode(log_event.output))
    except Exception as e:
        logger.error(f"Error in get_nb_tokens_completion_tokens: {e}")

    return 0


def collect_metadata(log_event: LogEvent) -> Optional[dict]:
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
    model: Optional[str] = metadata.get("model", None)
    tokenizer = None

    if "prompt_tokens" not in metadata.keys():
        metadata["prompt_tokens"] = get_nb_tokens_prompt_tokens(
            log_event, model, tokenizer
        )

    if "completion_tokens" not in metadata.keys():
        metadata["completion_tokens"] = get_nb_tokens_completion_tokens(
            log_event, model, tokenizer
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
            metadata["total_tokens"] = metadata.get("prompt_tokens", 0) + metadata.get(
                "completion_tokens", 0
            )

    return metadata


async def add_vectorized_tasks(
    tasks_id: List[str],
):
    mongo_db = await get_mongo_db()
    qdrant_db = await get_qdrant()
    # Get tasks
    tasks = await mongo_db["tasks"].find({"id": {"$in": tasks_id}}).to_list(length=None)
    tasks = [Task.model_validate(task) for task in tasks]

    openai_client = openai.AsyncClient()

    # Create tasks_text representations
    tasks_text = [f"{task.input} {task.output}" for task in tasks]
    try:
        # TODO : count the number of token for each task_text and if it's too big, do something smart
        embedding = await openai_client.embeddings.create(
            input=tasks_text, model="text-embedding-3-small"
        )
    except openai.APIError as e:
        logger.warning(f"Error while embedding the tasks: {e}")
        return

    try:
        await qdrant_db.upsert(
            collection_name="tasks",
            points=[
                models.PointStruct(
                    id=task.id,
                    vector=embedding.embedding,
                    payload={
                        "task_id": task.id,
                        "project_id": task.project_id,
                        "session_id": task.session_id,
                    },
                )
                for task, embedding in zip(tasks, embedding.data)
            ],
        )
    except Exception as e:
        logger.warning(f"Error while adding the tasks to Qdrant: {e}")
        return


def create_task_from_logevent(
    org_id: str,
    project_id: str,
    log_event: LogEvent,
    session_id: Optional[str] = None,
) -> Task:
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
        metadata=collect_metadata(log_event),
        data=None,
        flag=log_event.flag,
        test_id=log_event.test_id,
    )
    return task


async def ignore_existing_tasks(
    tasks_to_create: List[Dict[str, object]],
) -> List[Dict[str, object]]:
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
    return new_tasks_to_create


async def process_log_without_session_id(
    project_id: str, org_id: str, list_of_log_event: List[LogEvent]
) -> None:
    """
    Process a list of log events without session_id
    """
    if len(list_of_log_event) == 0:
        logger.debug("No log event without session_id to process")
        return None

    mongo_db = await get_mongo_db()

    tasks_id_to_process: List[str] = []
    tasks_to_create: List[Dict[str, object]] = []
    for log_event in list_of_log_event:
        task = create_task_from_logevent(
            org_id=org_id,
            project_id=project_id,
            log_event=log_event,
            session_id=None,
        )
        tasks_id_to_process.append(task.id)
        tasks_to_create.append(task.model_dump())

    # Skip task creation if there is no task to create
    if len(tasks_to_create) == 0:
        logger.debug("No task to create")
        return None

    # Create the tasks
    tasks_to_create = await ignore_existing_tasks(tasks_to_create)
    if len(tasks_to_create) > 0:
        await mongo_db["tasks"].insert_many(tasks_to_create)

    # Vectorize them
    await add_vectorized_tasks(tasks_id_to_process)

    # Trigger the pipeline
    for task_id in tasks_id_to_process:
        # Fetch the task data from the database
        # For now it's a double call to the database, but it's not a big deal
        task_data = await get_task_by_id(task_id)
        logger.info(f"Logevent: pipeline triggered for task {task_id}")
        await main_pipeline(task_data)

    return None


async def process_log_with_session_id(
    project_id: str, org_id: str, list_of_log_event: List[LogEvent]
) -> None:
    """
    Process a list of log events with session_id
    """
    if len(list_of_log_event) == 0:
        logger.debug("No log event with session_id to process")
        return None

    tasks_id_to_process: List[str] = []
    tasks_to_create: List[Dict[str, object]] = []
    sessions_to_create: Dict[str, Dict[str, Any]] = {}
    sessions_to_earliest_task: Dict[str, Task] = {}

    mongo_db = await get_mongo_db()

    sessions_id_already_in_db = (
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
    sessions_id_already_in_db = [session["id"] for session in sessions_id_already_in_db]

    for log_event in list_of_log_event:
        if log_event.project_id is None:
            log_event.project_id = project_id

        # Only create a new session if the session doesn't exist in db
        existing_session = log_event.session_id in sessions_id_already_in_db

        session_project_id = project_id
        if log_event.project_id is not None:
            session_project_id = log_event.project_id

        if not existing_session and log_event.session_id is not None:
            # Add to sessions to create
            session_data: Dict[str, Any] = {
                "id": log_event.session_id,
                "project_id": session_project_id,
                # Note: there is no metadata and data
                "metadata": {},
                "data": {},
            }
            # The sessions will be created later, once we know the earliest task creation time
            sessions_to_create[log_event.session_id] = session_data
        else:
            logger.info(
                f"Logevent: session with session_id {log_event.session_id} already exists (skipping session creation)"
            )

        task = create_task_from_logevent(
            org_id=org_id,
            project_id=log_event.project_id,
            log_event=log_event,
            session_id=log_event.session_id,
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
    tasks_to_create = await ignore_existing_tasks(tasks_to_create)
    if len(tasks_to_create) > 0:
        await mongo_db["tasks"].insert_many(tasks_to_create)

    # Add sessions to database
    if len(sessions_to_create) > 0:
        sessions_to_create_dump: List[dict] = []
        for session_id, session_data in sessions_to_create.items():
            # logger.info(
            #     f"Logevent: creating session with session_id {session_id} from log event"
            # )
            # Verify if the session already exists
            existing_session = session_id in sessions_id_already_in_db
            if existing_session:
                logger.info(
                    f"Logevent: session with session_id {session_id} already exists (skipping creation)"
                )
                continue
            else:
                session = Session(
                    id=session_id,
                    created_at=sessions_to_earliest_task[session_id].created_at,
                    project_id=session_data["project_id"],
                    org_id=org_id,
                    metadata=session_data["metadata"],
                    data=session_data["data"],
                    preview=sessions_to_earliest_task[session_id].preview(),
                )
                sessions_to_create_dump.append(session.model_dump())

        if len(sessions_to_create_dump) > 0:
            logger.info(
                f"Creating sessions: {' '.join([session_id for session_id in sessions_to_create.keys()])}"
            )
            insert_result = await mongo_db["sessions"].insert_many(
                sessions_to_create_dump
            )
            logger.info(f"Created {len(insert_result.inserted_ids)} sessions")
    else:
        logger.info("Logevent: no session to create")

    # Vectorize them
    await add_vectorized_tasks(tasks_id_to_process)

    # Trigger the pipeline
    for task_id in tasks_id_to_process:
        # Fetch the task data from the database
        # For now it's a double call to the database, but it's not a big deal
        task_data = await get_task_by_id(task_id)
        await main_pipeline(task_data)


async def process_log(
    project_id: str, org_id: str, logs_to_process: List[LogEvent]
) -> None:
    """From logs
    - Create Tasks
    - Create a Session
    - Trigger the Tasks processing pipeline
    """
    mongo_db = await get_mongo_db()
    logger.info(f"Logevent: processing {len(logs_to_process)} log events")

    def log_is_error(log_event):
        if isinstance(log_event, dict) and "Error in log" in log_event:
            return True
        return False

    nonerror_log_events = [
        log_event
        for log_event in logs_to_process
        if not log_is_error(log_event) and isinstance(log_event, LogEvent)
    ]
    logger.info(f"Logevent: saving {len(nonerror_log_events)} non-error log events")

    # Save the non-error log events
    if len(nonerror_log_events) > 0:
        mongo_db["logs"].insert_many(
            [log_event.model_dump() for log_event in nonerror_log_events]
        )

    # Process logs without session_id
    await process_log_without_session_id(
        project_id=project_id,
        org_id=org_id,
        list_of_log_event=[
            log_event
            for log_event in nonerror_log_events
            if log_event.session_id is None
        ],
    )

    # Process logs with session_id
    await process_log_with_session_id(
        project_id=project_id,
        org_id=org_id,
        list_of_log_event=[
            log_event
            for log_event in nonerror_log_events
            if log_event.session_id is not None
        ],
    )

    return None
