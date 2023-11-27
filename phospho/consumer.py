from .log_queue import LogQueue
from .client import Client

import time
import atexit
from threading import Thread

import logging

logger = logging.getLogger("phospho")


class Consumer(Thread):
    """Every tick, the consumer tries to send the accumulated logs to the backend."""

    def __init__(
        self,
        log_queue: LogQueue,
        client: Client,
        verbose: bool = True,
        tick: float = 0.5,  # How often to try to send logs
    ) -> None:
        self.running = True
        self.log_queue = log_queue
        self.client = client
        self.verbose = verbose
        self.tick = tick

        Thread.__init__(self, daemon=True)
        atexit.register(self.stop)

    def run(self) -> None:
        while self.running:
            self.send_batch()
            time.sleep(self.tick)

        self.send_batch()

    def send_batch(self) -> None:
        batch = self.log_queue.get_batch()
        logger.debug(f"Batch: {batch}")

        if len(batch) > 0:
            if self.verbose:
                logger.info(
                    f"Sending {len(batch)} log events to {self.client.base_url}"
                )

            try:
                self.client._post(
                    f"/log/{self.client._project_id()}", {"batched_log_events": batch}
                )
            except Exception as e:
                if self.verbose:
                    logger.warning(f"Error sending log events: {e}")

                # Put all the events back into the log queue, so they are logged next tick
                self.log_queue.add_batch(batch)

    def stop(self):
        self.running = False
        self.join()
