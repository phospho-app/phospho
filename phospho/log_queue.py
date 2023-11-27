import threading
import pydantic
from collections import defaultdict
from typing import Dict, Any, List

from .utils import generate_uuid


class Event(pydantic.BaseModel, extra="allow"):
    id: str
    content: Dict[str, object]
    to_log: bool = True


class LogQueue:
    """Queue logs here to group them in batchs"""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.events: Dict[str, Event] = {}

    def append(self, event: Event) -> None:
        with self.lock:
            self.events[event.id] = event

    def extend(self, events_queue: Dict[str, Event]) -> None:
        with self.lock:
            self.events.update(events_queue)

    def add_batch(self, events_content_list: List[Dict[str, object]]) -> None:
        with self.lock:
            # Create new event with id task_id
            def get_event_id(event: object) -> str:
                assert isinstance(event, dict)
                task_id = str(event.get("task_id", generate_uuid()))
                return task_id

            new_events: Dict[str, Event] = {
                get_event_id(event_content): Event(
                    to_log=True,
                    id=get_event_id(event_content),
                    content=event_content,
                )
                for event_content in events_content_list
            }
            self.events.update(new_events)

    def get_batch(self) -> List[Dict[str, object]]:
        if self.lock.acquire(False):  # non-blocking
            try:
                # Separate only events to log
                events_to_log = filter(lambda e: e.to_log, self.events.values())
                # Only keep events _not_ to log
                self.events = dict(
                    filter(lambda pair: not pair[1].to_log, self.events.items())
                )
                return [e.content for e in events_to_log]
            finally:
                self.lock.release()
        else:
            return []
