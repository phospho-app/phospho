import time
import traceback
from typing import Callable, List, Optional, Union

import httpx
import stripe
from app.api.v2.models import LogEvent, PipelineResults
from app.api.v3.models import MinimalLogEvent
from app.core import config
from app.db.models import Recipe, Task
from app.security import propelauth
from app.services.slack import slack_notification
from app.utils import generate_uuid, health_check
from loguru import logger

from phospho.lab import Message


def check_health_extractor():
    """
    Check if the extractor server is healthy
    """
    extractor_is_healthy = health_check(f"{config.EXTRACTOR_URL}/v1/health")
    if not extractor_is_healthy:
        logger.error(f"Extractor server is not reachable at url {config.EXTRACTOR_URL}")
    else:
        logger.info(f"Extractor server is reachable at url {config.EXTRACTOR_URL}")


async def bill_on_stripe(
    org_id: str,
    nb_credits_used: int,
    meter_event_name: str = "phospho_usage_based_meter",
) -> None:
    """
    Bill an organization on Stripe based on the consumption
    """
    if nb_credits_used == 0:
        logger.debug(f"No job results to bill for organization {org_id}")
        return

    if config.ENVIRONMENT == "preview" or config.ENVIRONMENT == "test":
        logger.debug("Preview environment, stripe billing disabled")
        return

    stripe.api_key = config.STRIPE_SECRET_KEY

    # Get the stripe customer id from the org metadata
    org = propelauth.fetch_org(org_id)
    org_metadata = org.get("metadata", {})
    customer_id = org_metadata.get("customer_id", None)

    if customer_id:
        stripe.billing.MeterEvent.create(
            event_name=meter_event_name,
            payload={
                "value": nb_credits_used,
                "stripe_customer_id": customer_id,
            },
            timestamp=int(time.time()),
        )
    elif org_id not in config.EXEMPTED_ORG_IDS:
        logger.error(f"Organization {org_id} has no stripe customer id")


class ExtractorClient:
    """
    A client to interact with the extractor server
    """

    def __init__(
        self,
        org_id: str,
        project_id: str,
    ):
        """
        project_id: Used to store and retrieve the logs

        org_id: Used to bill the organization on Stripe
        """
        self.org_id = org_id
        self.project_id = project_id

    async def _post(
        self,
        endpoint: str,
        data: dict,
        on_success_callback: Optional[Callable] = None,
    ) -> Optional[httpx.Response]:
        """
        Post data to the extractor server
        """
        url = f"{config.EXTRACTOR_URL}/v1/{endpoint}"
        headers = {
            "Authorization": f"Bearer {config.EXTRACTOR_SECRET_KEY}",
            "Content-Type": "application/json",
        }
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    url, json=data, headers=headers, timeout=60
                )
                if response.status_code != 200:
                    logger.error(
                        f"Error returned when calling extractor API (status code: {response.status_code}): {response.text}"
                    )
                    # If we are in production, send a Slack message
                    if config.ENVIRONMENT == "production":
                        await slack_notification(
                            f"Error returned when calling extractor API (status code: {response.status_code}): {response.text}"
                        )
                if response.status_code == 200 and on_success_callback:
                    await on_success_callback(response)

                return response
            except Exception as e:
                error_id = generate_uuid()
                error_message = f"Caught error while calling extractor API (error_id: {error_id}): {e}\n{traceback.format_exception(e)}"
                logger.error(error_message)

                traceback.print_exc()
                if config.ENVIRONMENT == "production":
                    if len(error_message) > 300:
                        slack_message = error_message[:300]
                    else:
                        slack_message = error_message
                    await slack_notification(slack_message)

        return None

    async def run_log_process_for_tasks(
        self,
        logs_to_process: List[LogEvent],
        extra_logs_to_save: Optional[List[LogEvent]] = None,
    ) -> None:
        """
        Run the log procesing pipeline on a task asynchronously
        """
        if extra_logs_to_save is None:
            extra_logs_to_save = []

        await self._post(
            "pipelines/log",
            {
                "logs_to_process": [
                    log_event.model_dump(mode="json") for log_event in logs_to_process
                ],
                "extra_logs_to_save": [
                    log_event.model_dump(mode="json")
                    for log_event in extra_logs_to_save
                ],
                "project_id": self.project_id,
                "org_id": self.org_id,
            },
            on_success_callback=lambda response: bill_on_stripe(
                org_id=self.org_id,
                nb_credits_used=response.json().get("nb_job_results", 0),
            ),
        )

    async def run_log_process_for_messages(
        self,
        logs_to_process: List[MinimalLogEvent],
        extra_logs_to_save: Optional[List[MinimalLogEvent]] = None,
    ):
        """
        Run the log procesing pipeline on *messages* asynchronously

        This is the v3 version of the function
        """
        if extra_logs_to_save is None:
            extra_logs_to_save = []

        await self._post(
            "pipelines/log/messages",
            {
                "logs_to_process": [
                    log_event.model_dump(mode="json") for log_event in logs_to_process
                ],
                "extra_logs_to_save": [
                    log_event.model_dump(mode="json")
                    for log_event in extra_logs_to_save
                ],
                "project_id": self.project_id,
                "org_id": self.org_id,
            },
            on_success_callback=lambda response: bill_on_stripe(
                org_id=self.org_id,
                nb_credits_used=response.json().get("nb_job_results", 0),
            ),
        )

    async def run_main_pipeline_on_task(self, task: Task) -> PipelineResults:
        """
        Run the log procesing pipeline on a task
        """
        result = await self._post(
            "pipelines/main/task",
            {
                "task": task.model_dump(mode="json"),
            },
        )
        if result is None or result.status_code != 200:
            return PipelineResults(events=[], flag=None)
        return PipelineResults.model_validate(result.json())

    async def run_main_pipeline_on_messages(
        self,
        messages: List[Message],
    ) -> PipelineResults:
        """
        Run the log procesing pipeline on messages asynchronously
        """

        if len(messages) == 0:
            logger.debug(f"No messages to process for project {self.project_id}")
            return PipelineResults(events=[], flag=None)

        result = await self._post(
            "pipelines/main/messages",
            {
                "messages": [message.model_dump(mode="json") for message in messages],
                "project_id": self.project_id,
            },
        )
        if result is None or result.status_code != 200:
            return PipelineResults(events=[], flag=None)
        return PipelineResults.model_validate(result.json())

    async def run_recipe_on_tasks(
        self,
        tasks: List[Task],
        recipe: Recipe,
    ):
        if len(tasks) == 0:
            logger.debug(f"No tasks to process for recipe {recipe.id}")
            return

        await self._post(
            "pipelines/recipes",
            {
                "tasks": [task.model_dump(mode="json") for task in tasks],
                "recipe": recipe.model_dump(mode="json"),
            },
            on_success_callback=lambda response: bill_on_stripe(
                org_id=self.org_id,
                nb_credits_used=response.json().get("nb_job_results", 0),
            ),
        )

    async def store_open_telemetry_data(
        self,
        open_telemetry_data: dict,
    ):
        await self._post(
            "pipelines/opentelemetry",
            {
                "open_telemetry_data": open_telemetry_data,
                "project_id": self.project_id,
                "org_id": self.org_id,
            },
        )

    async def collect_langsmith_data(
        self,
        current_usage: int,
        langsmith_api_key: Optional[str] = None,
        langsmith_project_name: Optional[str] = None,
        max_usage: Optional[int] = None,
    ):
        await self._post(
            "pipelines/langsmith",
            {
                "langsmith_api_key": langsmith_api_key,
                "langsmith_project_name": langsmith_project_name,
                "project_id": self.project_id,
                "org_id": self.org_id,
                "current_usage": current_usage,
                "max_usage": max_usage,
            },
            on_success_callback=lambda response: bill_on_stripe(
                org_id=self.org_id,
                nb_credits_used=response.json().get("nb_job_results", 0),
            ),
        )

    async def collect_langfuse_data(
        self,
        current_usage: int,
        langfuse_secret_key: Optional[str] = None,
        langfuse_public_key: Optional[str] = None,
        max_usage: Optional[int] = None,
    ):
        await self._post(
            "pipelines/langfuse",
            {
                "langfuse_secret_key": langfuse_secret_key,
                "langfuse_public_key": langfuse_public_key,
                "project_id": self.project_id,
                "org_id": self.org_id,
                "current_usage": current_usage,
                "max_usage": max_usage,
            },
            on_success_callback=lambda response: bill_on_stripe(
                org_id=self.org_id,
                nb_credits_used=response.json().get("nb_job_results", 0),
            ),
        )
