import argilla as rg
import pandas as pd
from app.api.platform.models.integrations import (
    DatasetCreationRequest,
    DatasetSamplingParameters,
    PowerBICredentials,
)
from app.services.mongo.projects import get_project_by_id
from loguru import logger
from app.core import config
from argilla import FeedbackDataset
from app.utils import health_check
from typing import List, Literal
from app.db.models import Task
from app.db.mongo import get_mongo_db
from app.core import constants
from app.services.mongo.tasks import get_total_nb_of_tasks
from app.services.mongo.explore import fetch_flattened_tasks
from app.api.platform.models import Pagination
from sqlalchemy import create_engine
from app.services.mongo.tasks import get_all_tasks

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


def sample_tasks(
    tasks: List[Task], sampling_params: DatasetSamplingParameters
) -> List[Task]:
    if sampling_params.sampling_type == "naive":
        return tasks

    if sampling_params.sampling_type == "balanced":
        logger.warning("Balanced sampling not implemented yet")
        return tasks

    return tasks


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

    # Add the no-event label (when no event is detected)
    labels["no-event"] = "No event"

    for key, value in project.settings.events.items():
        # We do not use session level events for now
        if value.detection_engine == "session":
            logger.debug(f"Skipping session event {key} as it is session level")
            continue
        labels[key] = key

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
            rg.RatingQuestion(
                name="sentiment",
                description="What is the sentiment of the message? (1: Very negative, 3: Neutral, 5: Very positive)",
                values=[1, 2, 3, 4, 5],
            ),
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
            rg.LabelQuestion(
                name="language",
                title="Language",
                description="Select the language of the user input",
                labels=constants.LANGUAGES_FOR_LABELLING,
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

    if len(tasks) <= config.MIN_NUMBER_OF_DATASET_SAMPLES:
        logger.warning(
            f"Not enough tasks found for project {creation_request.project_id} and filters {creation_request.filters} and limit {creation_request.limit}"
        )
        return None

    logger.debug(f"Found {len(tasks)} tasks for project {creation_request.project_id}")
    logger.debug(tasks[0].events)

    # Filter the sampling of tasks based on the dataset creation request
    if creation_request.sampling_parameters.sampling_type == "naive":
        sampled_tasks = tasks
    elif creation_request.sampling_parameters.sampling_type == "balanced":
        # Build the pandas dataframe
        df_records = []
        for task in tasks:
            df_record = {
                "user_input": task.input if task.input is not None else "",
                "assistant_output": task.output if task.output is not None else "",
                "task_id": task.id,
            }
            for label in labels:
                df_record[label] = False

            for event in task.events:
                if event.event_definition.detection_scope == "session":
                    continue
                df_record[event.event_definition.event_name] = True

            df_records.append(df_record)

        df = pd.DataFrame(df_records)

        labels_to_balance = list(labels.keys()).copy()

        while len(labels_to_balance) > 0:
            # Get the label with the least number of True values
            label = min(labels_to_balance, key=lambda x: df[x].sum())
            labels_to_balance.remove(label)

            logger.debug(f"Balancing label {label}")

            # Get the number of True values
            n_true = df[label].sum()

            # Get the number of False values
            n_false = len(df) - n_true

            # Get the number of samples to keep
            n_samples = min(n_true, n_false)

            if n_samples <= config.MIN_NUMBER_OF_DATASET_SAMPLES:
                logger.warning(f"Cannot balance label {label} with {n_samples} samples")
                continue

            logger.debug(f"Balancing label {label} with {n_samples} samples")

            # Balance the dataset
            df = pd.concat(
                [
                    df[df[label]].sample(n=n_samples),
                    df[df[label]].sample(n=n_samples),
                ]
            )

        sampled_tasks = [task for task in tasks if task.id in df["task_id"].tolist()]
        logger.info(
            f"Balanced dataset has {len(sampled_tasks)} tasks (compared to {len(tasks)} before balancing"
        )

    else:
        raise ValueError("Unknown sampling type. Must be naive or balanced.")

    # Make them into Argilla records
    records = []
    for task in sampled_tasks:
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
    argilla_dataset.push_to_argilla(
        name=creation_request.dataset_name, workspace=creation_request.workspace_id
    )

    logger.info(f"dataset : {argilla_dataset}")

    # TODO: add rules
    return argilla_dataset


async def get_power_bi_credentials(org_id: str) -> PowerBICredentials:
    mongo_db = await get_mongo_db()

    dedicated_db = await mongo_db["integrations"].find_one(
        {"org_id": org_id},
    )
    del dedicated_db["_id"]

    validated_db = PowerBICredentials.model_validate(dedicated_db)

    return validated_db


async def update_power_bi_status(
    org_id: str, project_id: str, status: Literal["started", "failed", "finished"]
) -> PowerBICredentials:
    mongo_db = await get_mongo_db()

    # Credentials have two array fields projects_started and projects_finished
    # We add the project_id to projects_started when the project is started
    # We remove the project_id from projects_started when the project is failed
    # We remove the project_id from projects_started and add it to projects_finished when the project is finished
    if status == "started":
        updated_credentials = await mongo_db["integrations"].find_one_and_update(
            {"org_id": org_id},
            {"$push": {"projects_started": project_id}},
            return_document=True,
        )
    elif status == "failed":
        updated_credentials = await mongo_db["integrations"].find_one_and_update(
            {"org_id": org_id},
            {"$pull": {"projects_started": project_id}},
            return_document=True,
        )
    else:  # status == "finished"
        updated_credentials = await mongo_db["integrations"].find_one_and_update(
            {"org_id": org_id},
            {
                "$pull": {"projects_started": project_id},
                "$push": {"projects_finished": project_id},
            },
            return_document=True,
        )

    return updated_credentials


async def export_project_to_dedicated_postgres(
    project_id: str, credentials: PowerBICredentials, debug: bool = False
) -> Literal["success", "failure"]:
    """
    Export the project to the dedicated Neon Postgres database
    """

    logger.info(
        f"Starting export of project {project_id} to dedicated Postgres {credentials.server}:{credentials.database}"
    )

    # Get the total number of tasks
    total_nb_tasks = await get_total_nb_of_tasks(project_id)

    # Connect to Neon Postgres database, we add asyncpg for ascync support
    connection_string = f"postgresql://{credentials.username}:{credentials.password}@{credentials.server}/{credentials.database}"
    engine = create_engine(connection_string, echo=debug)

    logger.debug(f"Connected to Postgres {credentials.server}:{credentials.database}")

    # We batch to avoid memory issues
    batch_size = 128
    nb_batches = total_nb_tasks // batch_size

    for i in range(nb_batches + 1):
        logger.debug(f"Exporting batch {i} of {nb_batches}")

        flattened_tasks = await fetch_flattened_tasks(
            project_id=project_id,
            limit=batch_size,
            with_events=True,
            with_sessions=True,
            pagination=Pagination(page=i, per_page=batch_size),
        )

        # Convert the list of FlattenedTask to a pandas dataframe
        tasks_df = pd.DataFrame(flattened_tasks)

        # row_fields is a tuple with (field_name, field)
        # We want to extract the field_name and keep the field_value
        row_fields = tasks_df.loc[0].to_dict()

        # We drop task_metadata for now because of the complexity of the dict format
        # Would require to add columns recursively as it can be a dict of dict of dict...
        columns_to_drop = []
        for i, field in row_fields.items():
            if "task_metadata" in field:
                # We drop the metadata field for now
                columns_to_drop.append(i)
            else:
                # We extract the field_name from the tuple and keep the value: (field_name, field_value)
                tasks_df[i] = tasks_df[i].apply(lambda x: x[1])

                # We rename the column with the field_name
                tasks_df.rename(columns={i: field[0]}, inplace=True)

        tasks_df.drop(columns=columns_to_drop, inplace=True)

        # Upload dataframe to Postgres
        # There should be no need to sleep in between batches, as this connector is synchronous
        pd.DataFrame.to_sql(tasks_df, "tasks", engine, if_exists="append", index=True)
        logger.debug(f"Uploaded batch {i} to Postgres")

    logger.info("Export finished")
    return "success"


"""
The function below is a work in progress to convert a Pydantic model to a SQLModel
Could be usefull later
"""

# def pydantic_to_sqlmodel(pydantic_model: BaseModel) -> Type[SQLModel]:
#     class_name = pydantic_model.__name__
#     columns = {}

#     for field_name, field in pydantic_model.model_fields.items():
#         field_type = field.annotation

#         string_field_type = str(field_type)

#         nullable = "Optional" in string_field_type

#         if "dict" in string_field_type or "Literal" in string_field_type:
#             continue

#         if field_name == "task_id":
#             columns[field_name] = (str, Field(primary_key=True))
#         else:
#             if "str" in string_field_type:
#                 columns[field_name] = (
#                     Optional[str] if nullable else str,
#                     Field(default=None, nullable=nullable),
#                 )
#             elif "int" in string_field_type:
#                 columns[field_name] = (
#                     Optional[int] if nullable else int,
#                     Field(default=None, nullable=nullable),
#                 )
#             elif "float" in string_field_type:
#                 columns[field_name] = (
#                     Optional[float] if nullable else float,
#                     Field(default=None, nullable=nullable),
#                 )
#             elif "bool" in string_field_type:
#                 columns[field_name] = (
#                     Optional[bool] if nullable else bool,
#                     Field(default=None, nullable=nullable),
#                 )
#             else:
#                 logger.warning(
#                     f"Field {field_name} has unknown type {string_field_type}"
#                 )
#         logger.debug(
#             f"Added column {field_name} with type {string_field_type}, nullable {nullable}"
#         )

#     logger.debug(f"Creating SQLModel {class_name} with columns {columns}")
#     dynamic_class = create_model(
#         class_name,
#         __base__=SQLModel,
#         __cls_kwargs__={"table": True, "extend_existing": True},
#         **columns,
#     )
#     logger.debug(f"Created SQLModel {dynamic_class}")
#     return dynamic_class
