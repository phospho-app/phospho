"""
A service to interact with the extractor server
"""

# TODO : Refacto

import traceback
from typing import List, Optional

import httpx
from app.api.v2.models import LogEvent, PipelineResults
from app.core import config
from app.db.models import Task, Job
from app.services.slack import slack_notification
from app.utils import generate_uuid
from loguru import logger

from phospho.lab import Message


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


async def run_job_on_tasks(task: Task, job: Job):
    async with httpx.AsyncClient() as client:
        logger.debug(
            f"Calling the extractor run_job_on_task API for job {job.id} on task {task.id} tasks at {config.EXTRACTOR_URL}/v1/pipelines/jobs"
        )
        try:
            response = await client.post(
                f"{config.EXTRACTOR_URL}/v1/pipelines/jobs",  # WARNING: hardcoded API version
                json={
                    "task": task.model_dump(),
                    "job": job.model_dump(),
                },
                headers={
                    "Authorization": f"Bearer {config.EXTRACTOR_SECRET_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=60,
            )
            if response.status_code != 200:
                logger.error(
                    f"Error returned when calling run job on task (status code: {response.status_code}): {response.text}"
                )
                # If we are in production, send a Slack message
                if config.ENVIRONMENT == "production":
                    await slack_notification(
                        f"Error returned when calling run job on task (status code: {response.status_code}): {response.text}"
                    )
        except Exception as e:
            errror_id = generate_uuid()
            error_message = f"Caught error while calling run job on task (error_id: {errror_id}): {e}\n{traceback.format_exception(e)}"
            logger.error(error_message)
