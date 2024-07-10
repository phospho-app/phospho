from app.services.mongo.tasks import get_all_tasks
from app.api.platform.models.datasets import DatasetCreationRequest
from loguru import logger
from app.core import config


def check_health_argilla():
    """
    Check if the Argilla server is configured and healthy
    """
    if config.ARGILLA_URL is None:
        logger.error("Argilla URL is not configured.")
        return False

    if config.ARGILLA_API_KEY is None:
        logger.error("Argilla API Key is not configured.")
        return False


async def generate_dataset_from_project(creation_request: DatasetCreationRequest):
    """
    Extract a dataset from a project and push it to Argilla
    """

    # For now, naive select
    # Get all the tasks of the project matching the filters and limit
    tasks = await get_all_tasks(
        project_id=creation_request.project_id,
        limit=creation_request.limit,
        filters=creation_request.filters,
    )

    logger.debug(f"Found {len(tasks)} tasks for project {creation_request.project_id}")
    logger.debug(tasks[0])

    # Load the project configs

    # Create the dataset
    # Add phospho metadata in the dataset metadata: org_id, project_id, filters, limit,...

    # Tasks to dataset records
    # task_id to the dataset record metatada (and other relevant data)

    #

    # TODO: add rules
    pass
