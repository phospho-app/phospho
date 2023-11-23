from .agent import Agent
from .message import Message
from .client import Client
from .consumer import Consumer
from .log_queue import LogQueue
from .utils import generate_timestamp, generate_uuid

import pydantic

from typing import Dict, Any, Optional, Union


client = None
log_queue = None
consumer = None
current_session_id = None
current_task_id = None


def init(verbose: bool = True, tick: float = 0.1) -> None:
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
    output: Union[Dict[str, Any], pydantic.BaseModel],
    session_id: Optional[str] = None,
    task_id: Optional[str] = None,
    step_id: Optional[str] = None,
    **kwargs,
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

    # Default session and task id
    if not session_id:
        # Reuse the existing id
        session_id = current_session_id
    else:
        # Update the current id
        current_session_id = session_id

    if not task_id:
        # Reuse the existing id
        task_id = current_task_id
    else:
        # Update the current id
        current_task_id = task_id

    # Process the input and output to convert them dict
    if isinstance(input, pydantic.BaseModel):
        input = input.model_dump()
    if isinstance(output, pydantic.BaseModel):
        output = output.model_dump()

    # The log event looks like this:
    log_event: Dict[str, object] = {
        "client_timestamp": generate_timestamp(),
        "project_id": client._project_id(),
        "session_id": session_id,
        "task_id": task_id,
        "step_id": step_id,
        "input": input,
        "output": output,
    }

    # Append event to log_queue
    log_queue.append(log_event)

    return log_event
