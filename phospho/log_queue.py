import threading


class LogQueue:
    """Queue logs here to group them in batchs"""

    def __init__(self):
        self.lock = threading.Lock()
        self.events = []

    def append(self, event):
        with self.lock:
            self.events.append(event)

    def get_batch(self):
        if self.lock.acquire(False):  # non-blocking
            try:
                events = self.events
                self.events = []
                return events
            finally:
                self.lock.release()
        else:
            return []
