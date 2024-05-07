"""
A service to interact with the extractor server
"""

# TODO : Refacto

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
) -> None:
    """
    Bill an organization on Stripe based on the consumption
    """
    if nb_credits_used == 0:
        logger.debug(f"No job results to bill for organization {org_id}")
        return

    stripe.api_key = config.STRIPE_SECRET_KEY

    # Get the stripe customer id from the org metadata
    org = propelauth.fetch_org(org_id)
    org_metadata = org.get("metadata", {})
    customer_id = org_metadata.get("customer_id", None)

    EXEMPTED_ORG_IDS = [
        "13b5f728-21a5-481d-82fa-0241ca0e07b9",  # phospho
        "bb46a507-19db-4e11-bf26-6bd7cdc8dcdd",  # e
        "a5724a02-a243-4025-9b34-080f40818a31",  # m
        "144df1a7-40f6-4c8d-a0a2-9ed010c1a142",  # v
        "3bf3f4b0-2ef7-47f7-a043-d96e9f5a3d7e",  # st
        "8e530a71-8739-450a-844a-5a6430067f9a",  # y
        "2fdbcf01-eb52-4747-bb14-b66621973e8f",  # sa
        "5a3d67ab-231c-4ad1-adba-84b6842668ad",  # sa (a)
        "7e8f6db2-3b6b-4bf6-84ee-3f226b81e43d",  # di
    ]

    if customer_id:
        stripe.billing.MeterEvent.create(
            event_name="phospho_usage_based_meter",
            payload={
                "value": nb_credits_used,
                "stripe_customer_id": customer_id,
            },
        )
    elif org_id not in EXEMPTED_ORG_IDS:
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
                        log_event.model_dump() for log_event in logs_to_process
                    ],
                    "extra_logs_to_save": [
                        log_event.model_dump() for log_event in extra_logs_to_save
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
            errror_id = generate_uuid()
            error_message = f"Caught error while calling main pipeline (error_id: {errror_id}): {e}\n{traceback.format_exception(e)}"
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
                    "task": task.model_dump(),
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
            errror_id = generate_uuid()
            error_message = f"Caught error while calling main pipeline (error_id: {errror_id}): {e}\n{traceback.format_exception(e)}"
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
                    "messages": [message.model_dump() for message in messages],
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
            errror_id = generate_uuid()
            error_message = f"Caught error while calling main pipeline (error_id: {errror_id}): {e}\n{traceback.format_exception(e)}"
            logger.error(error_message)

            traceback.print_exc()
            if config.ENVIRONMENT == "production":
                if len(error_message) > 200:
                    slack_message = error_message[:200]
                else:
                    slack_message = error_message
                await slack_notification(slack_message)
            return PipelineResults(events=[], flag=None)


async def run_recipe_on_tasks(tasks: List[Task], recipe: Recipe):
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
                    "tasks": [task.model_dump() for task in tasks],
                    "recipe": recipe.model_dump(),
                },
                headers={
                    "Authorization": f"Bearer {config.EXTRACTOR_SECRET_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=60,
            )
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
            errror_id = generate_uuid()
            error_message = f"Caught error while calling run recipe on task (error_id: {errror_id}): {e}\n{traceback.format_exception(e)}"
            logger.error(error_message)
