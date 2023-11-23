from .agent import Agent
from .message import Message
from .client import Client
from .consumer import Consumer
from .log_queue import LogQueue
from .utils import generate_timestamp, generate_uuid, filter_nonjsonable_keys

import pydantic
import logging

from typing import Dict, Any, Optional, Union


client = None
log_queue = None
consumer = None
current_session_id = None
current_task_id = None

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
    input: Union[Dict[str, Any], pydantic.BaseModel],
    output: Optional[Union[Dict[str, Any], pydantic.BaseModel]] = None,
    session_id: Optional[str] = None,
    task_id: Optional[str] = None,
    step_id: Optional[str] = None,
    **kwargs: Dict[str, Any],
) -> Dict[str, object]:
    """Main logging endpoint

    Returns: What have been logged
    """
    global client
    global log_queue
    global current_session_id
    global current_task_id

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

    # Process the input and output to convert them dict
    if isinstance(input, pydantic.BaseModel):
        input_to_log = input.model_dump()
    else:
        input_to_log = input
    if output is not None:
        if isinstance(output, pydantic.BaseModel):
            output_to_log = output.model_dump()
        else:
            output_to_log = output
    else:
        output_to_log = None

    # Every other kwargs will be directly stored in the logs, if it's json serializable
    if kwargs:
        original_keys = set(kwargs.keys())
        # Filter the keys to only keep the ones that json serializable
        kwargs_to_log = filter_nonjsonable_keys(kwargs)
        new_keys = set(kwargs_to_log.keys())
        dropped_keys = original_keys - new_keys
        if dropped_keys:
            logger.warning(
                f"Logging skipped for the keys that aren't json serializable (no .toJSON() method): {', '.join(dropped_keys)}"
            )
    else:
        kwargs_to_log = {}

    # The log event looks like this:
    log_event: Dict[str, object] = {
        "client_timestamp": generate_timestamp(),
        "project_id": client._project_id(),
        "session_id": session_id,
        "task_id": task_id,
        "step_id": step_id,
        "input": input_to_log,
        "input_type_name": type(input).__name__,
        "output": output_to_log,
        "output_type_name": type(output).__name__,
        **kwargs_to_log,
    }

    # Append event to log_queue
    log_queue.append(log_event)

    return log_event
