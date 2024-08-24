import hashlib
import time
import traceback
from typing import Callable, List, Optional

import httpx
import stripe

from app.api.v2.models import LogEvent
from app.api.v3.models import MinimalLogEventForMessages
from app.core import config
from app.services.slack import slack_notification
from app.utils import generate_uuid
from app.temporal.pydantic_converter import pydantic_data_converter
from app.security import propelauth
from loguru import logger

from phospho.lab import Message
from phospho.models import PipelineResults, Recipe, Task

from temporalio.client import Client, TLSConfig

import os
from hashlib import sha1


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


async def fetch_stripe_customer_id(org_id: str) -> Optional[str]:
    """
    Fetch the Stripe customer id from the organization metadata
    """

    if config.ENVIRONMENT == "preview" or config.ENVIRONMENT == "test":
        logger.debug("Preview environment, stripe billing disabled")
        return None

    org = propelauth.fetch_org(org_id)
    org_metadata = org.get("metadata", {})
    return org_metadata.get("customer_id", None)


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
        endpoint: str,  # Should be the name of the workflow
        data: dict,  # Should be just one pydantic model
        on_success_callback: Optional[Callable] = None,
    ) -> Optional[httpx.Response]:
        """
        Post data to the extractor server
        """

        # We check that "org_id", "project_id" and "customer_id" are present in the data
        if endpoint not in ["store_open_telemetry_data_workflow"] and (
            self.org_id is None or self.project_id is None
        ):
            logger.error(
                f"Missing org_id, project_id or customer_id for endpoint {endpoint}"
            )
            return None

        # We add this data for the extractor server
        data["org_id"] = self.org_id
        data["project_id"] = self.project_id
        data["customer_id"] = await fetch_stripe_customer_id(self.org_id)

        try:
            client_cert = config.TEMPORAL_MTLS_TLS_CERT
            client_key = config.TEMPORAL_MTLS_TLS_KEY

            client: Client = await Client.connect(
                os.getenv("TEMPORAL_HOST_URL"),
                namespace=os.getenv("TEMPORAL_NAMESPACE"),
                tls=TLSConfig(
                    client_cert=client_cert,
                    client_private_key=client_key,
                ),
                data_converter=pydantic_data_converter,
            )

            # Hash the data to generate a unique determinist id
            unique_id = (
                endpoint
                + hashlib.md5(
                    repr(sorted(data.items())).encode("utf-8"),
                    usedforsecurity=False,
                ).hexdigest()
            )

            response = await client.execute_workflow(
                endpoint, data, id=unique_id, task_queue="default"
            )

            if on_success_callback:
                await on_success_callback(response)

        except Exception as e:
            error_id = generate_uuid()
            error_message = (
                f"Caught error while calling temporal workflow {endpoint} "
                + f"(error_id: {error_id} project_id: {self.project_id} organisation_id: {self.org_id} workflow_id: {unique_id}):"
                + f"{e}\n{traceback.format_exception(e)}"
            )
            logger.error(error_message)

            traceback.print_exc()
            if config.ENVIRONMENT == "production":
                if len(error_message) > 800:
                    slack_message = error_message[:800]
                else:
                    slack_message = error_message
                await slack_notification(slack_message)

        return None

    async def run_process_log_for_tasks(
        self,
        logs_to_process: List[LogEvent],
        extra_logs_to_save: Optional[List[LogEvent]] = None,
    ) -> None:
        """
        Run the log procesing pipeline on a task asynchronously
        """
        if extra_logs_to_save is None:
            extra_logs_to_save = []

        # Ignore the intermediate_inputs of log_events because it's too big
        # They are collected in the Langchain integration
        # TODO: Fix this
        for log_event in logs_to_process:
            # Remove additional_inputs.intermediate_inputs from the log_event if it exists
            if hasattr(log_event, "raw_input"):
                if (
                    isinstance(log_event.raw_input, dict)
                    and "intermediate_inputs" in log_event.raw_input.keys()
                ):
                    logger.info(
                        f"Removing intermediate_inputs from log_event project {self.project_id}"
                    )
                    del log_event.raw_input["intermediate_inputs"]
            if hasattr(log_event, "raw_output"):
                if (
                    isinstance(log_event.raw_output, dict)
                    and "intermediate_outputs" in log_event.raw_output.keys()
                ):
                    logger.info(
                        f"Removing intermediate_outputs from log_event project {self.project_id}"
                    )

                    del log_event.raw_output["intermediate_outputs"]

        await self._post(
            "run_process_log_for_tasks_workflow",
            {
                "logs_to_process": [
                    log_event.model_dump(mode="json") for log_event in logs_to_process
                ],
                "extra_logs_to_save": [
                    log_event.model_dump(mode="json")
                    for log_event in extra_logs_to_save
                ],
            },
        )

    async def run_log_process_for_messages(
        self,
        logs_to_process: List[MinimalLogEventForMessages],
        extra_logs_to_save: Optional[List[MinimalLogEventForMessages]] = None,
    ):
        """
        Run the log procesing pipeline on *messages* asynchronously

        This is the v3 version of the function
        """
        if extra_logs_to_save is None:
            extra_logs_to_save = []

        await self._post(
            "run_process_logs_for_messages_workflow",
            {
                "logs_to_process": [
                    log_event.model_dump(mode="json") for log_event in logs_to_process
                ],
                "extra_logs_to_save": [
                    log_event.model_dump(mode="json")
                    for log_event in extra_logs_to_save
                ],
            },
        )

    async def run_main_pipeline_on_task(self, task: Task) -> PipelineResults:
        """
        Run the log procesing pipeline on a task
        """

        if task.org_id is None:
            logger.error("Task.org_id is missing.")
            return PipelineResults()

        result = await self._post(
            "run_main_pipeline_on_task_workflow",
            {
                "task": task.model_dump(mode="json"),
            },
        )
        if result is None or result.status_code != 200:
            return PipelineResults()
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
            return PipelineResults()

        if self.org_id is None:
            logger.error("Org_id is missing.")
            return PipelineResults()

        result = await self._post(
            "run_main_pipeline_on_messages_workflow",
            {
                "messages": [message.model_dump(mode="json") for message in messages],
            },
        )
        if result is None or result.status_code != 200:
            return PipelineResults()

        return PipelineResults.model_validate(result.json())

    async def run_recipe_on_tasks(
        self,
        tasks_ids: List[str],
        recipe: Recipe,
    ):
        if len(tasks_ids) == 0:
            logger.debug(f"No tasks to process for recipe {recipe.id}")
            return

        if recipe.org_id is None:
            logger.error("recipe.org_id is missing.")
        else:
            await self._post(
                "run_recipe_on_task_workflow",
                {
                    "tasks_ids": tasks_ids,
                    "recipe": recipe.model_dump(mode="json"),
                },
            )

    async def store_open_telemetry_data(
        self,
        open_telemetry_data: dict,
    ):
        await self._post(
            "store_open_telemetry_data_workflow",
            {
                "open_telemetry_data": open_telemetry_data,
                # No customer_id because we don't bill for open telemetry data, we simply log
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
            "extract_langsmith_data_workflow",
            {
                "langsmith_api_key": langsmith_api_key,
                "langsmith_project_name": langsmith_project_name,
                "current_usage": current_usage,
                "max_usage": max_usage,
            },
        )

    async def collect_langfuse_data(
        self,
        current_usage: int,
        langfuse_secret_key: Optional[str] = None,
        langfuse_public_key: Optional[str] = None,
        max_usage: Optional[int] = None,
    ):
        await self._post(
            "extract_langfuse_data_workflow",
            {
                "langfuse_secret_key": langfuse_secret_key,
                "langfuse_public_key": langfuse_public_key,
                "current_usage": current_usage,
                "max_usage": max_usage,
            },
        )
