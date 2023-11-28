from .agent import Agent
from .message import Message
from .client import Client
from .consumer import Consumer
from .log_queue import LogQueue, Event
from .utils import generate_timestamp, generate_uuid, convert_to_jsonable_dict
from .extractor import get_input_output, RawDataType
from .config import BASE_URL
from ._version import __version__

import logging

from typing import Dict, Any, Optional, Union, Callable, Tuple


client = None
log_queue = None
consumer = None
current_session_id = None
verbose = True

logger = logging.getLogger(__name__)


def init(
    api_key: Optional[str] = None,
    project_id: Optional[str] = None,
    verbose: bool = True,
    tick: float = 0.5,
) -> None:
    """
    Initialize the phospho logging module.

    This sets up a log_queue, stored in memory, and a consumer. Calls to `phospho.log()`
    push logs content to the log_queue. Every tick, the consumer tries to push the content
    of the log_queue to the phospho backend.

    api_key: Phospho API key
    project_id: Phospho project id
    verbose: whether to display logs
    tick: how frequently the consumer tries to push logs to the backend (in seconds)
    """
    global client
    global log_queue
    global consumer
    global current_session_id

    client = Client(api_key=api_key, project_id=project_id)
    log_queue = LogQueue()
    consumer = Consumer(log_queue=log_queue, client=client, verbose=verbose, tick=tick)
    # Start the consumer on a separate thread (this will periodically send logs to backend)
    consumer.start()

    # Initialize session and task id
    if current_session_id is None:
        current_session_id = generate_uuid()


def new_session() -> str:
    """
    Sessions are used to group tasks and logs together.

    Use `phospho.new_session()` when you start a new conversation. All the following
    calls to phospho.log() will be linked to this `session_id`.

    Alternatively, store `session_id` yourself, and pass the `session_id` parameter to
    override `phospho.log` default behaviour:
    ```
    phospho.log("stuff", session_id="custom_session_id")
    ```

    Returns the new session_id.
    """
    global current_session_id
    current_session_id = generate_uuid()
    return current_session_id


def log(
    input: Union[RawDataType, str],
    output: Optional[Union[RawDataType, str]] = None,
    session_id: Optional[str] = None,
    task_id: Optional[str] = None,
    raw_input: Optional[RawDataType] = None,
    raw_output: Optional[RawDataType] = None,
    input_to_str_function: Optional[Callable[[Any], str]] = None,
    output_to_str_function: Optional[Callable[[Any], str]] = None,
    output_to_task_id_and_to_log_function: Optional[
        Callable[[Any], Tuple[Optional[str], bool]]
    ] = None,
    concatenate_raw_outputs_if_task_id_exists: bool = True,
    to_log: bool = True,
    **kwargs: Dict[str, Any],
) -> Dict[str, object]:
    """Phospho's main all-purpose logging endpoint. Usage:
    ```
    phospho.log(input="input", output="output")
    ```

    By default, phospho will try to interpret a string representation from `input` and `output`.
    For example, OpenAI API calls. Arguments passed as `input` and `output` are then stored
    in `raw_input` and `raw_output`, unless those are specified.

    You can customize this behaviour using `input_to_str_function` and `output_to_str_function`.

    `session_id` is used to group logs together. For example, a single conversation.

    By default, every log is assigned to a unique `task_id` and is immediately pushed to backend.
    However, if you pass multiple logs with the same `task_id` and `to_log=False`, they will
    stay in queue until they receive the same `task_id` with `to_log=False`. They will then
    be combined and pushed to backend.
    You can automate this behaviour using `output_to_task_id_and_to_log_function`. This is used
    to handle streaming.

    Every other `**kwargs` will be added to the log content and stored.

    Returns: Dict[str, object] The content of what has been logged.
    """
    global client
    global log_queue
    global current_session_id
    global verbose

    assert (
        (log_queue is not None) and (client is not None)
    ), "phospho.log() was called but the global variable log_queue was not found. Make sure that phospho.init() was called."

    # Session: if nothing specified, reuse existing id. Otherwise, update current id
    if not session_id:
        session_id = current_session_id
    else:
        current_session_id = session_id

    # Process the input and output to convert them to dict
    (
        input_to_log,
        output_to_log,
        raw_input_to_log,
        raw_output_to_log,
        task_id_from_output,
        extracted_to_log,
    ) = get_input_output(
        input=input,
        output=output,
        raw_input=raw_input,
        raw_output=raw_output,
        input_to_str_function=input_to_str_function,
        output_to_str_function=output_to_str_function,
        output_to_task_id_and_to_log_function=output_to_task_id_and_to_log_function,
        verbose=verbose,
    )

    # Override to_log parameter
    if extracted_to_log is not None:
        to_log = extracted_to_log

    # Task: use the task_id parameter, the task_id infered from inputs, or generate one
    if task_id is None:
        if task_id_from_output is None:
            # if nothing specified, create new id.
            task_id = generate_uuid()
        else:
            task_id = task_id_from_output

    # Every other kwargs will be directly stored in the logs, if it's json serializable
    if kwargs:
        kwargs_to_log = convert_to_jsonable_dict(kwargs, verbose=verbose)
    else:
        kwargs_to_log = {}

    # The log event looks like this:
    log_content: Dict[str, object] = {
        "client_created_at": generate_timestamp(),
        # metadata
        "project_id": client._project_id(),
        "session_id": session_id,
        "task_id": task_id,
        # input
        "input": str(input_to_log),
        "raw_input": raw_input_to_log,
        "raw_input_type_name": type(input).__name__,
        # output
        "output": output_to_log,
        "raw_output": raw_output_to_log,
        "raw_output_type_name": type(output).__name__,
        # other
        **kwargs_to_log,
    }

    logger.debug(f"Existing task_id: {list(log_queue.events.keys())}")
    logger.debug(f"Current task_id: {task_id}")

    if task_id in log_queue.events.keys():
        # If the task_id already exists in log_queue, update the existing event content
        # Update the dict inplace
        existing_log_content = log_queue.events[task_id].content
        fused_log_content = {
            # Replace creation timestamp by the original one
            # Keep a trace of the latest timestamp. This will help computing streaming time
            "client_created_at": existing_log_content["client_created_at"],
            "last_update": log_content["client_created_at"],
            # Concatenate the log event output strings
            "output": str(existing_log_content["output"]) + str(log_content["output"])
            if (
                existing_log_content["output"] is not None
                and log_content["output"] is not None
            )
            else log_content["output"],
            "raw_output": [
                existing_log_content["raw_output"],
                log_content["raw_output"],
            ]
            if not isinstance(existing_log_content["raw_output"], list)
            else existing_log_content["raw_output"] + [log_content["raw_output"]],
        }
        # TODO : Turn this bool into a parametrizable list
        if concatenate_raw_outputs_if_task_id_exists:
            log_content.pop("raw_output")
        existing_log_content.update(log_content)
        existing_log_content.update(fused_log_content)
        # Concatenate the raw_outputs to keep all the intermediate results to openai
        if concatenate_raw_outputs_if_task_id_exists:
            if isinstance(existing_log_content["raw_output"], list):
                existing_log_content["raw_output"].append(raw_output_to_log)
            else:
                existing_log_content["raw_output"] = [
                    existing_log_content["raw_output"],
                    raw_output_to_log,
                ]
        log_content = existing_log_content
        # Update the to_log status of event
        log_queue.events[task_id].to_log = to_log
    else:
        # Append event to log_queue
        log_queue.append(event=Event(id=task_id, content=log_content, to_log=to_log))

    logger.debug("Updated dict:" + str(log_queue.events[task_id].content))
    logger.debug("To log" + str(log_queue.events[task_id].to_log))

    return log_content


log
