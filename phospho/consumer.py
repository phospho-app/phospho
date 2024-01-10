from .log_queue import LogQueue
from .client import Client

import time
import atexit
import os
from threading import Thread

import logging

logger = logging.getLogger(__name__)


class Consumer(Thread):
    """Every tick, the consumer tries to send the accumulated logs to the backend."""

    def __init__(
        self,
        log_queue: LogQueue,
        client: Client,
        tick: float = 0.5,  # How often to try to send logs
        raise_error_on_fail_to_send: bool = False,
    ) -> None:
        self.running = True
        self.log_queue = log_queue
        self.client = client
        self.tick = tick
        self.raise_error_on_fail_to_send = raise_error_on_fail_to_send

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
            logger.debug(f"Sending {len(batch)} log events to {self.client.base_url}")

            try:
                PHOSPHO_TEST_ID = os.getenv("PHOSPHO_TEST_ID")
                PHOSPHO_TEST_METRIC = os.getenv("PHOSPHO_TEST_METRIC")
                if PHOSPHO_TEST_ID is None:
                    # Normal behaviour : send logs to backend
                    self.client._post(
                        f"/log/{self.client._project_id()}",
                        {"batched_log_events": batch},
                    )
                elif PHOSPHO_TEST_ID is not None:
                    # Test mode: send logs if we are in the right metric
                    if PHOSPHO_TEST_METRIC == "evaluate":
                        # Add the test_id to the log events
                        for event in batch:
                            event["test_id"] = PHOSPHO_TEST_ID
                        self.client._post(
                            f"/log/{self.client._project_id()}",
                            {"batched_log_events": batch},
                        )
            except Exception as e:
                logger.warning(f"Error sending log events: {e}")

                if self.raise_error_on_fail_to_send:
                    # If we are in a test, we want to raise the error
                    raise e
                else:
                    # Put all the events back into the log queue, so they are logged next tick
                    self.log_queue.add_batch(batch)

    def stop(self):
        self.running = False
        self.join()
