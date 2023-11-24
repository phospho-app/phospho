from .agent import Agent
from .message import Message
from .client import Client
from .consumer import Consumer
from .log_queue import LogQueue
from .utils import generate_timestamp, generate_uuid, convert_to_jsonable_dict
from .extractor import get_input_output, RawDataType

import logging

from typing import Dict, Any, Optional, Union, Callable


client = None
log_queue = None
consumer = None
current_session_id = None
current_task_id = None
verbose = True

logger = logging.getLogger("phospho")


def init(verbose: bool = True, tick: float = 0.5) -> None:
    global client
    global log_queue
    global consumer
    global current_session_id
    global current_task_id

    client = Client()
    log_queue = LogQueue()
    consumer = Consumer(log_queue=log_queue, client=client, verbose=verbose, tick=tick)
    # Start the consumer on a separate thread (this will periodically send logs to backend)
    consumer.start()

    # Initialize session and task id
    if current_session_id is None:
        current_session_id = generate_uuid()
    if current_task_id is None:
        current_task_id = generate_uuid()


def log(
    input: Union[RawDataType, str],
    output: Optional[Union[RawDataType, str]] = None,
    session_id: Optional[str] = None,
    task_id: Optional[str] = None,
    step_id: Optional[str] = None,
    raw_input: Optional[RawDataType] = None,
    raw_output: Optional[RawDataType] = None,
    input_to_str_function: Optional[Callable[[Any], str]] = None,
    output_to_str_function: Optional[Callable[[Any], str]] = None,
    **kwargs: Dict[str, Any],
) -> Dict[str, object]:
    """Main logging endpoint

    Returns: What has been logged
    """
    global client
    global log_queue
    global current_session_id
    global current_task_id
    global verbose

    assert (
        (log_queue is not None) and (client is not None)
    ), "phospho.log() was called but the global variable log_queue was not found. Make sure that phospho.init() was called."

    # Session: if nothing specified, reuse existing id. Otherwise, update current id
    if not session_id:
        session_id = current_session_id
    else:
        current_session_id = session_id
    # Task: if nothing specified, reuse existing id. Otherwise, update current id
    if not task_id:
        task_id = current_task_id
    else:
        current_task_id = task_id
    # Step: if nothing specified, create new id.
    if step_id is None:
        step_id = generate_uuid()

    # Process the input and output to convert them to dict
    input_to_log, output_to_log, raw_input_to_log, raw_output_to_log = get_input_output(
        input=input,
        output=output,
        raw_input=raw_input,
        raw_output=raw_output,
        input_to_str_function=input_to_str_function,
        output_to_str_function=output_to_str_function,
        verbose=verbose,
    )

    # Every other kwargs will be directly stored in the logs, if it's json serializable
    if kwargs:
        kwargs_to_log = convert_to_jsonable_dict(kwargs, verbose=verbose)
    else:
        kwargs_to_log = {}

    # The log event looks like this:
    log_event: Dict[str, object] = {
        "client_created_at": generate_timestamp(),
        # metadata
        "project_id": client._project_id(),
        "session_id": session_id,
        "task_id": task_id,
        "step_id": step_id,
        # input
        "input": str(input_to_log),
        "raw_input": raw_input_to_log,
        "raw_input_type_name": type(input).__name__,
        # output
        "output": str(output_to_log),
        "raw_output": raw_output_to_log,
        "raw_output_type_name": type(output).__name__,
        # other
        **kwargs_to_log,
    }

    # Append event to log_queue
    log_queue.append(log_event)

    return log_event
