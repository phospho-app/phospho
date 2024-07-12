from app.services.mongo.tasks import get_all_tasks
from app.api.platform.models.datasets import DatasetCreationRequest
from app.services.mongo.projects import get_project_by_id
from loguru import logger
from app.core import config
from argilla import FeedbackDataset
import argilla as rg
from app.utils import health_check
from typing import List

# Connect to argila
try:
    rg.init(api_url=config.ARGILLA_URL, api_key=config.ARGILLA_API_KEY)
except Exception as e:
    logger.error(e)


def check_health_argilla() -> None:
    """
    Check if the Argilla server is configured and healthy
    """
    if config.ARGILLA_URL is None:
        logger.error("Argilla URL is not configured.")

    if config.ARGILLA_API_KEY is None:
        logger.error("Argilla API Key is not configured.")

    is_reachable = health_check(f"{config.ARGILLA_URL}/api/_status")

    if is_reachable:
        logger.info(f"Argilla server is reachable at url {config.ARGILLA_URL}")
    else:
        logger.error(f"Argilla server is not reachable at url {config.ARGILLA_URL}")


def get_workspace_datasets(workspace_id: str) -> List[FeedbackDataset]:
    """
    Get the datasets of a workspace
    """
    try:
        datasets = rg.FeedbackDataset.list(workspace=workspace_id)
        return datasets
    except Exception as e:
        logger.error(e)
        return []


def dataset_name_is_valid(dataset_name: str, workspace_id: str) -> bool:
    """
    For now, checks if the name does not already exist in the workspace
    """
    if len(dataset_name) == 0:
        return False

    # Get the dataset names of this workspace
    try:
        dataset_list = rg.FeedbackDataset.list(
            workspace=workspace_id
        )  # This line will raise an exception if the workspace does not exist
        if dataset_name in [dataset.name for dataset in dataset_list]:
            return False

        return True

    except Exception as e:
        logger.warning(e)
        return False


async def generate_dataset_from_project(
    creation_request: DatasetCreationRequest,
) -> FeedbackDataset:
    """
    Extract a dataset from a project and push it to Argilla
    """
    # Load the project configs, so we know the dataset fields and questions
    project = await get_project_by_id(creation_request.project_id)

    logger.debug(f"events: {project.settings.events}")

    logger.debug(project)

    # Get the labels from the project settings
    # By default project.settings.events is {}
    labels = {}
    for key, value in project.settings.events.items():
        labels[key] = key

    # Get the number of keys in the labels
    nb_labels = len(labels.keys())

    if len(labels.keys()) < 2:
        logger.warning(
            f"Not enough labels found in project settings {project.id} with filters {creation_request.filters} and limit {creation_request.limit}"
        )
        return None

    # Create the dataset
    # Add phospho metadata in the dataset metadata: org_id, project_id, filters, limit,...
    # FeedbackDataset
    argilla_dataset = rg.FeedbackDataset(
        fields=[
            rg.TextField(
                name="user_input", title="User Input", required=True, use_markdown=True
            ),
            rg.TextField(
                name="assistant_output",
                title="Assistant Output",
                required=True,
                use_markdown=True,
            ),
        ],
        questions=[
            rg.MultiLabelQuestion(
                name="event_detection",
                title="Event detection",
                description="Select all the events that apply",
                labels=labels,
                required=True,
                visible_labels=max(
                    3, len(labels)
                ),  # The min number of labels to display must be equal or greater than 3
            ),
            rg.LabelQuestion(
                name="evaluation",
                title="Evaluation",
                description="Evaluate the quality of the assistant's response",
                labels=["Success", "Failure"],
                required=False,
            ),
            rg.TextQuestion(
                name="comment",
                title="Comment",
                description="Please provide any additional feedback",
                required=False,
            ),
        ],
        metadata_properties=[
            rg.TermsMetadataProperty(
                name="org_id",
                title="Organization ID",
                values=[project.org_id],
            ),
            rg.TermsMetadataProperty(
                name="project_id",
                title="Project ID",
                values=[creation_request.project_id],
            ),
        ],
    )

    # Tasks to dataset records
    # task_id to the dataset record metatada (and other relevant data)
    # For now, naive select
    # Get all the tasks of the project matching the filters and limit
    tasks = await get_all_tasks(
        project_id=creation_request.project_id,
        limit=creation_request.limit,
        filters=creation_request.filters,
    )

    if len(tasks) <= 2:
        logger.warning(
            f"Not enough tasks found for project {creation_request.project_id} and filters {creation_request.filters} and limit {creation_request.limit}"
        )
        return None

    logger.debug(f"Found {len(tasks)} tasks for project {creation_request.project_id}")
    logger.debug(tasks[0])

    # Make them into Argilla records
    records = []
    for task in tasks:
        record = rg.FeedbackRecord(
            fields={
                "user_input": task.input,
                "assistant_output": task.output,
            },
            metadata={"task_id": task.id},
        )
        records.append(record)

    print(f"loaded {len(records)} records")

    argilla_dataset.add_records(records)

    # Push the dataset to Argilla
    remote_dataset = argilla_dataset.push_to_argilla(
        name=creation_request.dataset_name, workspace=creation_request.workspace_id
    )

    logger.info(f"dataset : {argilla_dataset}")

    # TODO: add rules
    return argilla_dataset
