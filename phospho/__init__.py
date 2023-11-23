from .agent import Agent
from .message import Message
from .client import Client
from .consumer import Consumer
from .log_queue import LogQueue
from .utils import generate_timestamp, generate_uuid

from typing import Dict, Any, Optional

print(globals())

client = None
log_queue = None
consumer = None
current_session_id = None
current_task_id = None


def init():
    global client
    global log_queue
    global consumer
    global current_session_id
    global current_task_id

    client = Client()
    log_queue = LogQueue()
    consumer = Consumer(log_queue=log_queue, client=client)
    # Start the consumer on a separate thread (this will periodically send logs to backend)
    consumer.start()

    if "current_session_id" not in globals():
        current_session_id = generate_uuid()
    if "current_task_id" not in globals():
        current_task_id = generate_uuid()


def log(
    input: Dict[str, Any],
    output: Dict[str, Any],
    session_id: Optional[str] = None,
    task_id: Optional[str] = None,
    step_id: Optional[str] = None,
    **kwargs,
):
    """Main logging endpoint"""
    global log_queue
    global current_session_id
    global current_task_id

    if "log_queue" not in globals():
        raise RuntimeError(
            "phospho.log() was called but the global variable log_queue was not found. Make sure that phospho.init() was called."
        )

    if not session_id:
        session_id = current_session_id
    if not current_task_id:
        session_id = current_session_id

    event = {
        "client_timestamp": generate_timestamp(),
        "session_id": session_id,
        "task_id": task_id,
        "step_id": step_id,
        "input": input,
        "output": output,
    }

    # Append event to log_queue
    log_queue.append(event)
    return event
