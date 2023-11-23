import threading

from typing import Dict, Any, List


class LogQueue:
    """Queue logs here to group them in batchs"""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.events: List[Dict[str, Any]] = []

    def append(self, event: Dict[str, Any]) -> None:
        with self.lock:
            self.events.append(event)

    def extend(self, events: List[Dict[str, Any]]) -> None:
        with self.lock:
            self.events.extend(events)

    def get_batch(self) -> List[Dict[str, Any]]:
        if self.lock.acquire(False):  # non-blocking
            try:
                events = self.events
                self.events = []  # Empty event list
                return events
            finally:
                self.lock.release()
        else:
            return []
