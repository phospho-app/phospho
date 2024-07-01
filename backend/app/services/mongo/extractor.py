"""
A service to interact with the extractor server
"""

# TODO : Refacto

import time
import traceback
from typing import List, Optional

import httpx
from app.api.v2.models import LogEvent, PipelineResults
from app.core import config
from app.db.models import Task, Recipe
from app.services.slack import slack_notification
from app.utils import generate_uuid
from loguru import logger

from phospho.lab import Message
from app.security import propelauth
import stripe


def health_check():
    """
    Check if the extractor server is healthy
    """
    try:
        response = httpx.get(f"{config.EXTRACTOR_URL}/v1/health")
        return response.status_code == 200
    except Exception as e:
        logger.error(e)
        return False


def check_health():
    """
    Check if the extractor server is healthy
    """
    extractor_is_healthy = health_check()
    if not extractor_is_healthy:
        logger.error(f"Extractor server is not reachable at url {config.EXTRACTOR_URL}")
    else:
        logger.debug(f"Extractor server is reachable at url {config.EXTRACTOR_URL}")


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

    if config.ENVIRONMENT == "preview":
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


async def run_log_process(
    logs_to_process: List[LogEvent],
    project_id: str,
    org_id: str,
    extra_logs_to_save: Optional[List[LogEvent]] = None,
):
    """
    Run the log procesing pipeline on a task asynchronously
    """
    if extra_logs_to_save is None:
        extra_logs_to_save = []

    # if len(logs_to_process) == 0:
    #     logger.debug(f"No logs to process for project {project_id}")
    #     return

    async with httpx.AsyncClient() as client:
        logger.debug(
            f"Calling the extractor API for {len(logs_to_process)} logevents, project {project_id} org {org_id}: {config.EXTRACTOR_URL}/v1/pipelines/log"
        )
        try:
            response = await client.post(
                f"{config.EXTRACTOR_URL}/v1/pipelines/log",  # WARNING: hardcoded API version
                json={
                    "logs_to_process": [
                        log_event.model_dump(mode="json")
                        for log_event in logs_to_process
                    ],
                    "extra_logs_to_save": [
                        log_event.model_dump(mode="json")
                        for log_event in extra_logs_to_save
                    ],
                    "project_id": project_id,
                    "org_id": org_id,
                },
                headers={
                    "Authorization": f"Bearer {config.EXTRACTOR_SECRET_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=60,
            )
            if response.status_code != 200:
                logger.error(
                    f"Error returned when calling main pipeline (status code: {response.status_code}): {response.text}"
                )
                # If we are in production, send a Slack message
                if config.ENVIRONMENT == "production":
                    await slack_notification(
                        f"Error returned when calling main pipeline (status code: {response.status_code}): {response.text}"
                    )
            if response.status_code == 200:
                # Bill the customer
                nb_job_results = response.json().get("nb_job_results", 0)
                await bill_on_stripe(org_id=org_id, nb_credits_used=nb_job_results)

        except Exception as e:
            error_id = generate_uuid()
            error_message = f"Caught error while calling main pipeline (error_id: {error_id}): {e}\n{traceback.format_exception(e)}"
            logger.error(error_message)

            traceback.print_exc()
            if config.ENVIRONMENT == "production":
                if len(error_message) > 200:
                    slack_message = error_message[:200]
                else:
                    slack_message = error_message
                await slack_notification(slack_message)


async def run_main_pipeline_on_task(task: Task) -> PipelineResults:
    """
    Run the log procesing pipeline on a task asynchronously
    """
    async with httpx.AsyncClient() as client:
        logger.debug(
            f"Calling the extractor API for task {task.id} logevents: {config.EXTRACTOR_URL}/v1/pipelines/log"
        )
        try:
            response = await client.post(
                f"{config.EXTRACTOR_URL}/v1/pipelines/main/task",  # WARNING: hardcoded API version
                json={
                    "task": task.model_dump(mode="json"),
                },
                headers={
                    "Authorization": f"Bearer {config.EXTRACTOR_SECRET_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=60,
            )
            if response.status_code != 200:
                logger.error(
                    f"Error returned when calling main pipeline (status code: {response.status_code}): {response.text}"
                )
                # If we are in production, send a Slack message
                if config.ENVIRONMENT == "production":
                    await slack_notification(
                        f"Error returned when calling main pipeline (status code: {response.status_code}): {response.text}"
                    )
            # Validate to Events
            pipeline_results = PipelineResults.model_validate(response.json())
            return pipeline_results
        except Exception as e:
            error_id = generate_uuid()
            error_message = f"Caught error while calling main pipeline (error_id: {error_id}): {e}\n{traceback.format_exception(e)}"
            logger.error(error_message)

            traceback.print_exc()
            if config.ENVIRONMENT == "production":
                if len(error_message) > 200:
                    slack_message = error_message[:200]
                else:
                    slack_message = error_message
                await slack_notification(slack_message)
            return PipelineResults(events=[], flag=None)


async def run_main_pipeline_on_messages(
    messages: List[Message], project_id: str
) -> PipelineResults:
    """
    Run the log procesing pipeline on messages asynchronously
    """

    if len(messages) == 0:
        logger.debug(f"No messages to process for project {project_id}")
        return PipelineResults(events=[], flag=None)

    async with httpx.AsyncClient() as client:
        logger.debug(
            f"Calling the extractor API for {len(messages)} messages: {config.EXTRACTOR_URL}/v1/pipelines/log"
        )
        try:
            response = await client.post(
                f"{config.EXTRACTOR_URL}/v1/pipelines/main/messages",  # WARNING: hardcoded API version
                json={
                    "messages": [
                        message.model_dump(mode="json") for message in messages
                    ],
                    "project_id": project_id,
                },
                headers={
                    "Authorization": f"Bearer {config.EXTRACTOR_SECRET_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=60,
            )
            if response.status_code != 200:
                logger.error(
                    f"Error returned when calling main pipeline (status code: {response.status_code}): {response.text}"
                )
                # If we are in production, send a Slack message
                if config.ENVIRONMENT == "production":
                    await slack_notification(
                        f"Error returned when calling main pipeline (status code: {response.status_code}): {response.text}"
                    )
            # Validate to Events
            pipeline_results = PipelineResults.model_validate(response.json())
            return pipeline_results
        except Exception as e:
            error_id = generate_uuid()
            error_message = f"Caught error while calling main pipeline (error_id: {error_id}): {e}\n{traceback.format_exception(e)}"
            logger.error(error_message)

            traceback.print_exc()
            if config.ENVIRONMENT == "production":
                if len(error_message) > 200:
                    slack_message = error_message[:200]
                else:
                    slack_message = error_message
                await slack_notification(slack_message)
            return PipelineResults(events=[], flag=None)


async def run_recipe_on_tasks(
    tasks: List[Task],
    recipe: Recipe,
    org_id: str,
):
    if len(tasks) == 0:
        logger.debug(f"No tasks to process for recipe {recipe.id}")
        return

    async with httpx.AsyncClient() as client:
        logger.debug(
            f"Calling the extractor run_recipe_on_task API for recipe {recipe.id} on {len(tasks)} tasks at {config.EXTRACTOR_URL}/v1/pipelines/recipes"
        )
        try:
            response = await client.post(
                f"{config.EXTRACTOR_URL}/v1/pipelines/recipes",  # WARNING: hardcoded API version
                json={
                    "tasks": [task.model_dump(mode="json") for task in tasks],
                    "recipe": recipe.model_dump(mode="json"),
                },
                headers={
                    "Authorization": f"Bearer {config.EXTRACTOR_SECRET_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=60,
            )
            if response.status_code == 200:
                # Bill the customer
                nb_job_results = response.json().get("nb_job_results", 0)
                await bill_on_stripe(org_id=org_id, nb_credits_used=nb_job_results)
            if response.status_code != 200:
                logger.error(
                    f"Error returned when calling run recipe on task (status code: {response.status_code}): {response.text}"
                )
                # If we are in production, send a Slack message
                if config.ENVIRONMENT == "production":
                    await slack_notification(
                        f"Error returned when calling run recipe on task (status code: {response.status_code}): {response.text}"
                    )
        except Exception as e:
            error_id = generate_uuid()
            error_message = f"Caught error while calling run recipe on task (error_id: {error_id}): {e}\n{traceback.format_exception(e)}"
            logger.error(error_message)


async def store_open_telemetry_data(
    open_telemetry_data: dict, project_id: str, org_id: str
):
    async with httpx.AsyncClient() as client:
        logger.debug(
            f"Calling the extractor API for storing opentelemetry data: {config.EXTRACTOR_URL}/v1/pipelines/opentelemetry"
        )
        try:
            response = await client.post(
                f"{config.EXTRACTOR_URL}/v1/pipelines/opentelemetry",  # WARNING: hardcoded API version
                json={
                    "open_telemetry_data": open_telemetry_data,
                    "project_id": project_id,
                    "org_id": org_id,
                },
                headers={
                    "Authorization": f"Bearer {config.EXTRACTOR_SECRET_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=60,
            )
            if response.status_code != 200:
                logger.error(
                    f"Error returned when storing opentelemetry data (status code: {response.status_code}): {response.text}"
                )

        except Exception as e:
            error_id = generate_uuid()
            error_message = f"Caught error while storing opentelemetry data (error_id: {error_id}): {e}\n{traceback.format_exception(e)}"
            logger.error(error_message)


async def collect_langsmith_data(
    project_id: str,
    org_id: str,
    langsmith_credentials: dict,
    current_usage: int,
    max_usage: int,
):
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{config.EXTRACTOR_URL}/v1/pipelines/langsmith",  # WARNING: hardcoded API version
                json={
                    "langsmith_credentials": langsmith_credentials,
                    "project_id": project_id,
                    "org_id": org_id,
                    "current_usage": current_usage,
                    "max_usage": max_usage,
                },
                headers={
                    "Authorization": f"Bearer {config.EXTRACTOR_SECRET_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=60,
            )
            if response.status_code != 200:
                logger.error(
                    f"Error returned when collecting langsmith data (status code: {response.status_code}): {response.text}"
                )

        except Exception as e:
            error_message = f"Caught error while collecting langsmith data: {e}\n{traceback.format_exception(e)}"
            logger.error(error_message)


async def collect_langfuse_data(
    project_id: str,
    org_id: str,
    langfuse_credentials: dict,
    current_usage: int,
    max_usage: int,
):
    async with httpx.AsyncClient() as client:
        logger.debug(
            f"Calling the extractor API for collecting langfuse data: {config.EXTRACTOR_URL}/v1/pipelines/langfuse"
        )
        try:
            response = await client.post(
                f"{config.EXTRACTOR_URL}/v1/pipelines/langfuse",  # WARNING: hardcoded API version
                json={
                    "langfuse_credentials": langfuse_credentials,
                    "project_id": project_id,
                    "org_id": org_id,
                    "current_usage": current_usage,
                    "max_usage": max_usage,
                },
                headers={
                    "Authorization": f"Bear {config.EXTRACTOR_SECRET_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=60,
            )
            if response.status_code != 200:
                logger.error(
                    f"Error returned when collecting langfuse data (status code: {response.status_code}): {response.text}"
                )

        except Exception as e:
            error_message = f"Caught error while collecting langfuse data: {e}\n{traceback.format_exception(e)}"
            logger.error(error_message)
