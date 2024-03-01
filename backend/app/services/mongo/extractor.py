"""
A service to interact with the extractor server behing this main app
"""

import httpx
from app.db.models import Task
from app.core import config
from loguru import logger
import traceback


from app.services.slack import slack_notification
from app.utils import generate_uuid


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


async def run_main_pipeline(task: Task):
    """
    Run the main pipeline on a task asynchronously
    """
    async with httpx.AsyncClient() as client:
        logger.debug(
            f"Calling the extractor API for task {task.id}: {config.EXTRACTOR_URL}/v1/pipelines/main"
        )
        try:
            response = await client.post(
                f"{config.EXTRACTOR_URL}/v1/pipelines/main",  # WARNING: hardcoded API version
                json={"task": task.model_dump()},
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
            logger.error(f"Task: {task}")
            traceback.print_exc()
            if config.ENVIRONMENT == "production":
                if len(error_message) > 200:
                    slack_message = error_message[:200]
                else:
                    slack_message = error_message
                await slack_notification(slack_message)
