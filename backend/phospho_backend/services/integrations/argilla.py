from phospho_backend.db.mongo import get_mongo_db
from phospho_backend.services.mongo.events import (
    change_label_event,
    change_value_event,
    confirm_event,
    get_event_definition_from_event_id,
    get_last_event_for_task,
    remove_event,
)
import argilla as rg  # type: ignore
import pandas as pd
from phospho_backend.api.platform.models.integrations import (
    DatasetCreationRequest,
    DatasetPullRequest,
    DatasetSamplingParameters,
)
from phospho_backend.services.mongo.projects import get_project_by_id
from loguru import logger
from phospho_backend.core import config
from argilla import FeedbackDataset
from phospho_backend.utils import health_check
from phospho_backend.db.models import Task
from phospho_backend.services.mongo.tasks import get_all_tasks
from phospho_backend.utils import generate_valid_name

from phospho.models import Event

# Connect to argilla
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
    if config.ARGILLA_URL is not None and config.ARGILLA_API_KEY is not None:
        is_reachable = health_check(f"{config.ARGILLA_URL}/api/_status")
        if is_reachable:
            logger.info(f"Argilla server is reachable at url {config.ARGILLA_URL}")
        else:
            logger.error(f"Argilla server is not reachable at url {config.ARGILLA_URL}")


def get_workspace_datasets(workspace_id: str) -> list[FeedbackDataset]:
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


def dataset_name_exists(dataset_name: str, workspace_id: str, project_id: str) -> bool:
    """
    For now, checks if the name does not already exist in the workspace
    """
    # Get the dataset names of this workspace
    try:
        dataset_list = rg.FeedbackDataset.list(
            workspace=workspace_id
        )  # This line will raise an exception if the workspace does not exist
        for dataset in dataset_list:
            if (
                dataset.name == dataset_name
                and dataset.metadata_properties[1].values[0] == project_id
            ):
                return True

        return False

    except Exception as e:
        logger.warning(e)
        return False


def get_datasets_name(workspace_id: str, project_id: str) -> list[str]:
    """
    Get the dataset names of this project
    """

    datasets = []
    # Get the dataset names of this workspace
    try:
        dataset_list = rg.FeedbackDataset.list(
            workspace=workspace_id
        )  # This line will raise an exception if the workspace does not exist
        for dataset in dataset_list:
            logger.debug(dataset.name)
            logger.debug(dataset.metadata_properties)
        for dataset in dataset_list:
            if (
                len(dataset.metadata_properties) > 0
                and dataset.metadata_properties[1].values[0] == project_id
            ):
                datasets.append(dataset.name)

        return datasets

    except Exception as e:
        logger.warning(e)
        return datasets


def sample_tasks(
    tasks: list[Task], sampling_params: DatasetSamplingParameters
) -> list[Task]:
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

    logger.debug(f"events: {project.settings.events}, project: {project}")

    # Get the labels from the project settings
    # By default project.settings.events is {}
    taggers = {}
    scorers: dict[str, list[int]] = {}
    classifiers = {}
    metadata_properties = [
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
    ]

    # Add the no-event label (when no event is detected)
    taggers["no-tag"] = "No tag"

    for key, value in project.settings.events.items():
        # Generate the metadata name following the regex pattern
        metadata_name = generate_valid_name(key, display_warning=True)
        if metadata_name != key:
            logger.warning(
                f"Changed metadata name to {metadata_name} (previously {key}) in project {project.id}"
            )
        # We do not use session level events for now
        if value.detection_engine == "session":
            logger.debug(f"Skipping session event {key} as it is session level")
            continue
        if value.score_range_settings.score_type == "confidence":
            taggers[key] = f"{key.replace(' ', '_').lower()}"
            metadata_properties.append(
                rg.TermsMetadataProperty(
                    name=metadata_name,
                    title=key,
                    values=[value.id],
                    visible_for_annotators=False,
                )
            )
        elif value.score_range_settings.score_type == "score":
            scorers[key] = [
                i
                for i in range(
                    int(value.score_range_settings.min),
                    int(value.score_range_settings.max),
                )
            ]
            metadata_properties.append(
                rg.TermsMetadataProperty(
                    name=metadata_name,
                    title=key,
                    values=[value.id],
                    visible_for_annotators=False,
                )
            )
        elif value.score_range_settings.score_type == "category":
            classifiers[key] = value.score_range_settings.categories
            metadata_properties.append(
                rg.TermsMetadataProperty(
                    name=metadata_name,
                    title=key,
                    values=[value.id],
                    visible_for_annotators=False,
                )
            )

    questions = []

    if len(taggers.keys()) > 2:
        questions.append(
            rg.MultiLabelQuestion(
                name="taggers",
                title="Taggers",
                description="Select all the tags that apply",
                labels=taggers,
                required=True,
                visible_labels=len(taggers),
            )
        )
    else:
        logger.warning(
            f"Not enough taggers found in project settings {project.id} with filters {creation_request.filters} and limit {creation_request.limit}"
        )

    # Create the dataset
    # Add phospho metadata in the dataset metadata: org_id, project_id, filters, limit,...
    # FeedbackDataset

    for key in scorers.keys():
        metadata_name = generate_valid_name(key, display_warning=True)

        questions.append(
            rg.RatingQuestion(
                name=metadata_name,
                title=key,
                description="Select the score",
                values=scorers[key],
                required=True,
            )
        )

    for key in classifiers.keys():
        logger.debug(f"classifiers: {classifiers[key]}")
        logger.debug(type(key))

    for key in classifiers.keys():
        metadata_name = generate_valid_name(key, display_warning=True)
        questions.append(
            rg.LabelQuestion(
                name=metadata_name,
                title=key,
                description="Select the category",
                labels=classifiers[key],
                required=True,
            )
        )

    questions.append(
        rg.TextQuestion(
            name="comment",
            title="Comment",
            description="Please provide any additional feedback",
            required=False,
        )
    )

    # Check if at least one question is required
    one_question_is_required = False
    for question in questions:
        if question.required:
            one_question_is_required = True
            break

    if not one_question_is_required:
        # We add an eval question that is required
        questions.append(
            rg.LabelQuestion(
                name="evaluation",
                title="evaluation",
                description="If you consider this interaction as a success, select 'Success'. If you consider it as a failure, select 'Failure'.",
                labels=["Success", "Failure"],
                required=True,
            )
        )

        logger.warning(
            f"No required question found in the project settings {project.id}. Dataset creation will be created anyway."
        )

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
        questions=questions,
        metadata_properties=metadata_properties,
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
            df_record: dict[str, object] = {
                "user_input": task.input if task.input is not None else "",
                "assistant_output": task.output if task.output is not None else "",
                "task_id": task.id,
            }
            for tag in taggers:
                df_record[tag] = False

            if task.events is not None:
                for event in task.events:
                    if (
                        event.event_definition is not None
                        and event.event_definition.detection_scope != "session"
                    ):
                        df_record[event.event_definition.event_name] = True

            df_records.append(df_record)

        df = pd.DataFrame(df_records)

        labels_to_balance = list(taggers.keys()).copy()
        while len(labels_to_balance) > 0:
            # Get the label with the least number of True values
            tag = min(labels_to_balance, key=lambda x: df[x].sum())
            labels_to_balance.remove(tag)

            logger.debug(f"Balancing label {tag}")
            # Get the number of True values
            n_true = df[tag].sum()
            # Get the number of False values
            n_false = len(df) - n_true
            # Get the number of samples to keep
            n_samples = min(n_true, n_false)

            if n_samples <= config.MIN_NUMBER_OF_DATASET_SAMPLES:
                logger.warning(f"Cannot balance label {tag} with {n_samples} samples")
                continue

            logger.debug(f"Balancing label {tag} with {n_samples} samples")
            # Balance the dataset
            df = pd.concat(
                [
                    df[df[tag]].sample(n=n_samples),
                    df[~df[tag]].sample(n=n_samples),
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


async def pull_dataset_from_argilla(
    pull_request: DatasetPullRequest,
) -> FeedbackDataset:
    """
    Extract a dataset from a project and push it to Argilla
    """

    # Load the project configs, so we know the dataset fields and questions
    await get_project_by_id(pull_request.project_id)

    argilla_dataset = rg.FeedbackDataset.from_argilla(
        name=pull_request.dataset_name, workspace=pull_request.workspace_id
    ).pull()

    # Get the event ids from the metadata properties
    original_events_ids = {}
    for i in range(2, len(argilla_dataset.metadata_properties)):
        event_name = argilla_dataset.metadata_properties[i].name
        event_definition_id = argilla_dataset.metadata_properties[i].values[0]
        original_events_ids[event_name] = event_definition_id

    # To detect that an event has been removed, we gather all the taggers in the questions.
    # If the tagger is not present in the annotated record, we will mark it as removed.
    original_taggers_list = []
    for key in argilla_dataset.questions[0].labels.keys():
        if key == "no-tag":
            continue
        original_taggers_list.append(generate_valid_name(key, display_warning=True))

    original_classifiers_and_scorers_list = []
    for i in range(1, len(argilla_dataset.questions) - 1):
        original_classifiers_and_scorers_list.append(
            argilla_dataset.questions[i].name.replace(" ", "_").lower()
        )

    mongo_db = await get_mongo_db()

    # # Fetch the relevant data in argilla records and transform them into a dict we can process
    for record in argilla_dataset.records:
        if len(record.responses) == 0:
            continue

        task_id = record.metadata["task_id"]
        # taggers is a list of taggers that are present in this task
        taggers: list[str] = record.responses[0].values["taggers"].value

        for tagger in original_taggers_list:
            event_definition_id = original_events_ids[tagger]
            event_definition = await get_event_definition_from_event_id(
                project_id=pull_request.project_id, event_id=event_definition_id
            )

            # Loading the most recent occurrence of this exact event for this task in the database
            last_event_in_db = await get_last_event_for_task(
                project_id=pull_request.project_id,
                event_name=event_definition.event_name,
                task_id=task_id,
            )

            if not last_event_in_db or last_event_in_db.removed is True:
                # Create the event
                if tagger not in taggers:
                    continue
                tagger = Event(
                    event_name=event_definition.event_name,
                    source="owner",
                    confirmed=True,
                    task_id=task_id,
                    project_id=pull_request.project_id,
                    event_definition=event_definition,
                )
                event_model = Event.model_validate(tagger)
                await mongo_db["events"].insert_one(tagger.model_dump())
            else:
                event_model = Event.model_validate(last_event_in_db)

                # Confirm the tagger event
                if tagger in taggers:
                    await confirm_event(
                        project_id=pull_request.project_id, event_id=event_model.id
                    )

                # Remove the tagger event
                else:
                    await remove_event(
                        project_id=pull_request.project_id, event_id=event_model.id
                    )

        for classifier_or_scorer in original_classifiers_and_scorers_list:
            event_definition_id = original_events_ids[classifier_or_scorer]
            event_definition = await get_event_definition_from_event_id(
                project_id=pull_request.project_id, event_id=event_definition_id
            )
            corrected_label_or_value: str | float = (
                record.responses[0].values[classifier_or_scorer].value
            )

            last_event_in_db = await get_last_event_for_task(
                project_id=pull_request.project_id,
                task_id=task_id,
                event_name=event_definition.event_name,
            )

            if not last_event_in_db or last_event_in_db.removed is True:
                new_event = Event(
                    event_name=event_definition.event_name,
                    source="owner",
                    confirmed=True,
                    task_id=task_id,
                    project_id=pull_request.project_id,
                    event_definition=event_definition,
                )
                event_model = Event.model_validate(new_event)
                await mongo_db["events"].insert_one(new_event.model_dump())
            else:
                event_model = Event.model_validate(last_event_in_db)

                # Edit the event. Note: this always confirm the event.
                if isinstance(corrected_label_or_value, str):
                    await change_label_event(
                        project_id=pull_request.project_id,
                        event_id=event_model.id,
                        new_label=corrected_label_or_value,
                    )

                elif isinstance(corrected_label_or_value, float):
                    await change_value_event(
                        project_id=pull_request.project_id,
                        event_id=event_model.id,
                        new_value=corrected_label_or_value,
                    )

    return argilla_dataset
