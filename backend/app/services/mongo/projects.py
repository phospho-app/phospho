import datetime
import io
from typing import Dict, List, Literal, Optional

from app.api.v2.models.embeddings import Embedding
from app.services.mongo.query_builder import QueryBuilder
import pandas as pd
import resend
from app.api.platform.models import Sorting, Pagination, UserMetadata
from app.core import config
from app.db.models import (
    Project,
    ProjectDataFilters,
    Recipe,
    Session,
    Task,
    Test,
    Event,
)
from app.db.mongo import get_mongo_db
from app.security.authentification import propelauth
from app.services.mongo.explore import fetch_flattened_tasks
from app.services.mongo.extractor import ExtractorClient
from app.services.mongo.metadata import fetch_users_metadata
from app.services.mongo.tasks import (
    get_all_tasks,
    label_sentiment_analysis,
)
from app.services.slack import slack_notification
from app.utils import (
    cast_datetime_or_timestamp_to_timestamp,
    generate_timestamp,
    generate_uuid,
)
from fastapi import HTTPException
from loguru import logger
from propelauth_fastapi import User  # type: ignore

from phospho.models import Cluster, Clustering, Threshold, EventDefinition


async def get_project_by_id(project_id: str) -> Project:
    mongo_db = await get_mongo_db()

    # project_data = await mongo_db["projects"].find_one({"id": project_id})
    project_data = (
        await mongo_db["projects"]
        .aggregate(
            [
                {"$match": {"id": project_id}},
                {
                    "$lookup": {
                        "from": "event_definitions",
                        "localField": "id",
                        "foreignField": "project_id",
                        "as": "settings.events",
                    }
                },
                # Filter the EventDefinitions mapping to keep only the ones that are not removed
                {
                    "$addFields": {
                        "settings.events": {
                            "$filter": {
                                "input": "$settings.events",
                                "as": "event",
                                "cond": {
                                    "$and": [
                                        {"$ne": ["$$event.removed", True]},
                                        {"$ne": ["$$event.event_name", None]},
                                    ]
                                },
                            }
                        }
                    }
                },
                # The lookup operation turns the events into an array of EventDefinitions
                # Convert into a Mapping {eventName: EventDefinition}
                {
                    "$addFields": {
                        "settings.events": {
                            # if the array is empty, return an empty object
                            "$cond": {
                                "if": {"$eq": [{"$size": "$settings.events"}, 0]},
                                "then": {},
                                "else": {
                                    "$arrayToObject": {
                                        "$map": {
                                            "input": "$settings.events",
                                            "as": "item",
                                            "in": {
                                                "k": "$$item.event_name",
                                                "v": "$$item",
                                            },
                                        }
                                    }
                                },
                            }
                        }
                    }
                },
            ]
        )
        .to_list(length=1)
    )

    if project_data is None or len(project_data) == 0:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
    project_data = project_data[0]
    if "_id" in project_data:
        del project_data["_id"]

    try:
        project = Project.from_previous(project_data)
        for event_name, event in project.settings.events.items():
            if not event.recipe_id:
                recipe = Recipe(
                    org_id=project.org_id,
                    project_id=project.id,
                    recipe_type="event_detection",
                    parameters=event.model_dump(),
                )
                mongo_db["recipes"].insert_one(recipe.model_dump())
                project.settings.events[event_name].recipe_id = recipe.id

        # If the project dict is different from project_data, update the project_data
        project_dump = project.model_dump()
        del project_dump["settings"]["events"]
        del project_data["settings"]["events"]
        if project_dump != project_data:
            logger.info(f"Updating project {project.id}: {project.model_dump()}")
            mongo_db["projects"].update_one(
                {"id": project_data["id"]}, {"$set": project_dump}
            )
    except Exception as e:
        logger.warning(
            f"Error validating model of project {project_data.get('id', None)}: {e}"
        )
        raise HTTPException(
            status_code=500, detail=f"Error validating project model: {e}"
        )

    return project


async def delete_project_from_id(project_id: str) -> bool:
    """
    Delete a project from its id.

    To delete a project related resources, use delete_project_related_resources
    """
    mongo_db = await get_mongo_db()
    delete_result = await mongo_db["projects"].delete_one({"id": project_id})
    status = delete_result.deleted_count > 0
    return status


async def delete_project_related_resources(project_id: str):
    """
    Delete all the resources related to a project, but not the project itself.
    """
    mongo_db = await get_mongo_db()
    # Delete the related collections
    collections = ["sessions", "tasks", "events", "evals", "logs"]
    for collection_name in collections:
        await mongo_db[collection_name].delete_many({"project_id": project_id})


async def update_project(project: Project, **kwargs) -> Project:
    """
    Update a project with the provided kwargs.

    TODO: Update only the fields that are provided in the kwargs and not the whole project
    otherwise creates mongoDB timeouts
    """
    mongo_db = await get_mongo_db()

    # Construct the payload of the update
    payload = {
        key: value
        for key, value in kwargs.items()
        if value is not None and key in Project.model_fields.keys()
    }
    updated_project_data = project.model_dump()
    updated_project_data.update(payload)

    if payload:
        updated_project = Project.from_previous(updated_project_data)

        if "sentiment_threshold" in payload.get("settings", {}):
            try:
                threshold = Threshold.model_validate(
                    payload["settings"]["sentiment_threshold"]
                )
                await label_sentiment_analysis(
                    project_id=project.id,
                    score_threshold=threshold.score,
                    magnitude_threshold=threshold.magnitude,
                )
            except KeyError:
                logger.error(
                    "Error updating sentiment threshold: missing score or magnitude"
                )

        if "events" in payload.get("settings", {}):
            # Create a new recipe for each event in the payload
            for event_name, event_definition in (
                payload.get("settings", {}).get("events", {}).items()
            ):
                try:
                    event_definition_model = EventDefinition.model_validate(
                        event_definition
                    )
                    recipe = Recipe(
                        org_id=project.org_id,
                        project_id=project.id,
                        recipe_type="event_detection",
                        parameters=event_definition_model.model_dump(),
                    )
                    mongo_db["recipes"].insert_one(recipe.model_dump())
                    updated_project.settings.events[event_name].recipe_id = recipe.id
                    event_definition_model.recipe_id = recipe.id
                    # update event_definition with event_id
                    mongo_db["event_definitions"].update_one(
                        {"project_id": project.id, "id": event_definition_model.id},
                        {"$set": event_definition_model.model_dump()},
                        upsert=True,
                    )
                except Exception as e:
                    logger.error(f"Error creating recipe for event {event_name}: {e}")

            # Detect if an event has been removed
            # Create a set of events that are NOT in the payload, but are in the current project, based on their id
            updated_project_events_ids = [
                event_definition.id
                for event_definition in updated_project.settings.events.values()
            ]

            for event_name, event_definition in project.settings.events.items():
                if event_definition.id not in updated_project_events_ids:
                    # Event has been removed
                    try:
                        event_definition.removed = True
                        mongo_db["event_definitions"].update_one(
                            {"project_id": project.id, "id": event_definition.id},
                            {"$set": event_definition.model_dump()},
                        )
                        logger.info(f"Event {event_definition.id} has been removed")
                    except Exception as e:
                        logger.error(f"Error removing event {event_definition.id}: {e}")

                    # Disable the recipe
                    try:
                        recipe = await mongo_db["recipes"].find_one(
                            {"id": event_definition.recipe_id}
                        )
                        recipe = Recipe.model_validate(recipe)
                        recipe.status = "deleted"
                        mongo_db["recipes"].update_one(
                            {"id": event_definition.recipe_id},
                            {"$set": recipe.model_dump()},
                        )
                    except Exception as e:
                        logger.error(
                            f"Error disabling recipe for event {event_name}: {e}"
                        )
                    # Remove all historical events
                    try:
                        mongo_db["events"].update_many(
                            {
                                "project_id": project.id,
                                "event_definition.id": event_definition.id,
                            },
                            {"$set": {"removed": True}},
                        )
                        logger.debug(
                            f"Removing all historical events for event {event_definition.id}"
                        )
                    except Exception as e:
                        logger.error(
                            f"Error removing all historical events for event {event_definition.id}: {e}"
                        )

        # Update the database
        await mongo_db["projects"].update_one(
            {"id": project.id}, {"$set": updated_project.model_dump()}
        )

    updated_project = await get_project_by_id(project.id)
    return updated_project


async def add_project_events(project_id: str, events: List[EventDefinition]) -> Project:
    mongo_db = await get_mongo_db()
    # Get the current events settings
    current_project = await get_project_by_id(project_id)
    logger.debug(f"Current project: {current_project}")
    if not current_project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    current_events = current_project.settings.events
    logger.debug(f"Current events: {current_events}")
    # Add the new events
    for event in events:
        current_events[event.event_name] = event
    # Update the project
    logger.debug(f"New events: {current_events}")
    await mongo_db["projects"].update_one(
        {"id": project_id},
        {
            "$set": {
                "settings.events": {
                    event_name: event_definition.model_dump()
                    for event_name, event_definition in current_events.items()
                }
            }
        },
    )
    if events:
        await mongo_db["event_definitions"].insert_many(
            [event.model_dump() for event in events]
        )
    else:
        logger.warning("No events to add")

    updated_project = await get_project_by_id(project_id)
    return updated_project


async def email_project_tasks(
    project_id: str,
    uid: str,
    limit: Optional[int] = 5_000,
):
    def send_error_message():
        # Send an error message to the user
        params = {
            "from": "phospho <contact@phospho.ai>",
            "to": [user.get("email")],
            "subject": "Error exporting your tasks",
            "html": f"""<p>Hello!<br><br>We could not export your tasks for the project with id {project_id} (timestamp: {datetime.datetime.now().isoformat()})</p>
            <p><br>Please contact the support at contact@phospho.ai</p>
            <p>Best,<br>
            The Phospho Team</p>
            """,
        }

        resend.Emails.send(params)
        logger.debug(f"Sent error message to user: {user.get('email')}")

    if config.ENVIRONMENT != "preview":
        # Get the user email
        user = propelauth.fetch_user_metadata_by_user_id(uid, include_orgs=False)

        # Use Resend to send the email
        resend.api_key = config.RESEND_API_KEY

        try:
            # Convert task list to Pandas DataFrame
            flattened_tasks = await fetch_flattened_tasks(
                project_id=project_id,
                limit=limit,
                with_events=True,
                with_sessions=True,
                with_removed_events=False,
            )
            tasks_df = pd.DataFrame(
                [flat_task.model_dump() for flat_task in flattened_tasks]
            )

            # Convert timestamps to datetime
            for col in [
                "task_created_at",
                "task_eval_at",
                "event_created_at",
            ]:
                if col in tasks_df.columns:
                    tasks_df[col] = pd.to_datetime(tasks_df[col], unit="s")

        except Exception as e:
            error_message = f"Error converting tasks to DataFrame for {user.get('email')} project id {project_id}: {e}"
            logger.error(error_message)
            await slack_notification(error_message)

        exports = []
        # Convert the DataFrame to a CSV string, then to bytes
        try:
            csv_string = tasks_df.to_csv(index=False)
            csv_bytes = csv_string.encode()
            exports.append(
                {
                    "filename": "tasks.csv",
                    "content": list(csv_bytes),
                }
            )
        except Exception as e:
            error_message = f"Error converting tasks to CSV for {user.get('email')} project id {project_id}: {e}"
            logger.error(error_message)
            await slack_notification(error_message)

        # Get the excel file buffer
        try:
            excel_buffer = io.BytesIO()
            tasks_df.to_excel(excel_buffer, index=False, engine="xlsxwriter")
            excel_data = excel_buffer.getvalue()
            # encoded_excel = base64.b64encode(excel_data).decode()
            exports.append(
                {
                    "filename": "tasks.xlsx",
                    "content": list(excel_data),
                }
            )
        except Exception as e:
            error_message = f"Error converting tasks to Excel for {user.get('email')} project id {project_id}: {e}"
            logger.error(error_message)
            await slack_notification(error_message)

        # TODO : Add .parquet file export for large datasets
        try:
            parquet_buffer = io.BytesIO()
            # For the parquet export, convert task_metadata to a string
            tasks_df["task_metadata"] = tasks_df["task_metadata"].apply(str)
            tasks_df.to_parquet(parquet_buffer, index=False)
            parquet_data = parquet_buffer.getvalue()
            exports.append(
                {
                    "filename": "tasks.parquet",
                    "content": list(parquet_data),
                }
            )
        except Exception as e:
            error_message = f"Error converting tasks to Parquet for {user.get('email')} project id {project_id}: {e}"
            logger.error(error_message)
            await slack_notification(error_message)

        # If no exports, send an error message
        if not exports:
            send_error_message()
            return

        params = {
            "from": "phospho <contact@phospho.ai>",
            "to": [user.get("email")],
            "subject": "Your data is ready",
            "html": f"""<p>Hello!<br><br>Please find your exported messages below for your project with id {project_id} (timestamp: {datetime.datetime.now().isoformat()})</p>
            <p><br>Let us know your thoughts about phospho! You can directly respond to this email address !</p>
            <p>Enjoy,<br>
            The Phospho Team</p>
            """,
            "attachments": exports,
        }

        try:
            resend.Emails.send(params)  # type: ignore
            logger.info(f"Successfully sent tasks by email to {user.get('email')}")
        except Exception as e:
            error_message = f"Error sending email to {user.get('email')} project_id {project_id}: {e}"
            logger.error(error_message)
            await slack_notification(error_message)
    else:
        logger.warning("Preview environment: emails disabled")


async def get_all_sessions(
    project_id: str,
    limit: int = 1000,
    filters: Optional[ProjectDataFilters] = None,
    get_events: bool = True,
    get_tasks: bool = False,
    pagination: Optional[Pagination] = None,
    sorting: Optional[List[Sorting]] = None,
) -> List[Session]:
    mongo_db = await get_mongo_db()

    query_builder = QueryBuilder(
        project_id=project_id,
        filters=filters,
        fetch_objects="sessions",
    )
    pipeline = await query_builder.build()

    # To avoid the sort to OOM on Serverless MongoDB executor, we restrain the pipeline to the necessary fields...
    if sorting is None:
        sorting_dict = {"created_at": -1}
    else:
        sorting_dict = {sort.id: 1 if sort.desc else -1 for sort in sorting}
    pipeline.extend(
        [
            {
                "$project": {
                    "id": 1,
                    **{sort_key: 1 for sort_key in sorting_dict.keys()},
                }
            },
            {"$sort": sorting_dict},
        ]
    )

    # Add pagination
    if pagination:
        logger.info(f"Adding pagination: {pagination}")
        pipeline.extend(
            [
                {"$skip": pagination.page * pagination.per_page},
                {"$limit": pagination.per_page},
            ]
        )

    # ... and then we add the lookup and the deduplication
    pipeline.extend(
        [
            {
                "$lookup": {
                    "from": "sessions",
                    "localField": "id",
                    "foreignField": "id",
                    "as": "sessions",
                }
            },
            # unwind the sessions array
            {"$unwind": "$sessions"},
            # Replace the root with the sessions
            {"$replaceRoot": {"newRoot": "$sessions"}},
        ]
    )
    if get_events:
        query_builder.merge_events(foreignField="session_id", force=True)
        query_builder.deduplicate_sessions_events()
    if get_tasks:
        query_builder.merge_tasks(force=True)

    sessions = await mongo_db["sessions"].aggregate(pipeline).to_list(length=limit)

    # Filter the _id field from the Sessions
    for session in sessions:
        session.pop("_id", None)
    sessions = [Session.model_validate(data) for data in sessions]
    return sessions


async def get_all_tests(project_id: str, limit: int = 1000) -> List[Test]:
    mongo_db = await get_mongo_db()
    tests = (
        await mongo_db["tests"]
        .find({"project_id": project_id})
        .sort("created_at", -1)
        .to_list(length=limit)
    )
    tests = [Test.model_validate(data) for data in tests]
    return tests


async def store_onboarding_survey(user: User, survey: dict):
    mongo_db = await get_mongo_db()
    doc = {
        "user_email": user.email,
        "created_at": generate_timestamp(),
        "survey": survey,
    }
    mongo_db["onboarding_surveys"].insert_one(doc)
    await slack_notification(f"New onboarding survey from {user.email}: {survey}")
    return


async def backcompute_recipe(
    job_id: str, tasks: List[Task], batch_size: int = 16
) -> None:
    """
    Run predictions for a job on all the tasks of a project that have not been processed yet.
    """
    mongo_db = await get_mongo_db()

    recipe = await mongo_db["recipes"].find_one({"id": job_id})
    recipe = Recipe.model_validate(recipe)

    # Get the task IDs that have already been processed for this job
    processed_task_ids = [
        result["task_id"]
        for result in await mongo_db["job_results"]
        .find({"job_metadata.recipe_id": recipe.id}, {"task_id": 1})
        .to_list(None)
    ]

    # Filter out the tasks that have already been processed
    tasks_to_process = [task for task in tasks if task.id not in processed_task_ids]

    # Send the task to the job pipeline of the extractor
    extractor_client = ExtractorClient(
        org_id=recipe.org_id,
        project_id=recipe.project_id,
    )
    for i in range(0, len(tasks_to_process), batch_size):
        tasks_batch = tasks_to_process[i : i + batch_size]
        await extractor_client.run_recipe_on_tasks(
            tasks_ids=[task.id for task in tasks_batch],
            recipe=recipe,
        )


async def backcompute_recipes(
    project_id: str,
    recipe_ids: List[str],
    filters: ProjectDataFilters,
    limit: int = 10000,
) -> None:
    """
    Run predictions for a list of jobs on all the tasks of a project that match the filters and that have not been processed yet.
    """

    # Filter the tasks from the filters

    # TODO: filter on user_id is not implemented
    # Will be ignored for now
    if filters.user_id:
        logger.warning("Filter on user_id is not implemented")

    tasks = await get_all_tasks(project_id=project_id, limit=limit, filters=filters)

    # For each job, run the job on the tasks
    for recipe_id in recipe_ids:
        await backcompute_recipe(recipe_id, tasks)


async def collect_languages(
    project_id: str,
) -> List[str]:
    """
    Collect all detected languages from the tasks of a project
    """
    mongo_db = await get_mongo_db()
    pipeline = [
        {"$match": {"project_id": project_id}},
        {"$group": {"_id": "$language", "count": {"$sum": 1}}},
        {"$sort": {"count": -1, "_id": 1}},
    ]
    languages = await mongo_db["tasks"].aggregate(pipeline).to_list(length=10)
    languages = [lang.get("_id") for lang in languages if lang.get("_id") is not None]
    logger.info(f"Languages detected in project {project_id}: {languages}")
    return languages


def only_keep_fields(data: Optional[dict], fields: List[str]) -> Optional[dict]:
    """
    Keep only the fields in the list in the data dict
    """
    if data is None:
        return None
    new_dict = {key: value for key, value in data.items() if key in fields}
    if len(new_dict) == 0:
        return None
    return new_dict


async def copy_template_project_to_new(
    project_id: str,
    org_id: str,
    template_name: Literal["history", "animals", "medical"] = "animals",
) -> None:
    """
    Populate the project project_id with the data from the template project template_name.
    """
    logger.info(f"Populating project {project_id} with default values")
    mongo_db = await get_mongo_db()

    # event_definition_id -> EventDefinition
    event_definition_pairs: Dict[str, EventDefinition] = {}
    event_pairs: Dict[str, Event] = {}
    task_pairs: Dict[str, Task] = {}
    session_pairs: Dict[str, Session] = {}
    # embedding_id -> Embedding
    embedding_pairs: Dict[str, Embedding] = {}
    cluster_pairs: Dict[str, Cluster] = {}
    clustering_pairs: Dict[str, Clustering] = {}

    if config.ENVIRONMENT == "production":
        template_name_to_project_id = {
            "history": "b161b57d6ae94e2ea41e31a88ffbe99b",
            "animals": "9812dc9ba7a9402283621e56b49a03c8",
            "medical": "856870f888d941d48316f70b575de0a1",
        }
    else:
        template_name_to_project_id = {
            "history": "4feeb60f97834502b8af822c09a43d17",
            "animals": "436a6aa53b8c49fe95cadc6297bcd6ec",
            "medical": "b85f4086435a425b8b1cca4d0988e0c1",
        }

    template_project_id = template_name_to_project_id.get(template_name)
    if template_project_id is None:
        raise ValueError(f"Template name {template_name} not found")

    # Verify that the template project exists
    await get_project_by_id(template_project_id)

    # Add sessions to the project
    sessions_in_template = await get_all_sessions(template_project_id, get_events=True)
    sessions: List[Session] = []
    for session in sessions_in_template:
        old_session_id = session.id
        session.id = generate_uuid()
        session.created_at = generate_timestamp()
        session.project_id = project_id
        session.org_id = org_id
        session_pairs[old_session_id] = session
        sessions.append(session)

    if len(sessions) > 0:
        await mongo_db["sessions"].insert_many(
            [session.model_dump() for session in sessions]
        )
    else:
        raise ValueError("No sessions found in the default project")

    # Add events definitions to the project
    event_definitions_in_template = (
        await mongo_db["event_definitions"]
        .find(
            {
                "project_id": template_project_id,
                "removed": {"$ne": True},
            }
        )
        .to_list(length=None)
    )
    event_definitions: List[EventDefinition] = []
    for event_definition in event_definitions_in_template:
        event_definition_model = EventDefinition.model_validate(event_definition)
        event_definition_pairs[event_definition_model.id] = event_definition_model
        event_definition_model.id = generate_uuid()
        event_definition_model.project_id = project_id
        event_definition_model.org_id = org_id
        event_definitions.append(event_definition_model)

    if len(event_definitions) > 0:
        await mongo_db["event_definitions"].insert_many(
            [event_definition.model_dump() for event_definition in event_definitions]
        )

    # Add tasks to the project
    tasks_in_template = await get_all_tasks(
        project_id=template_project_id, get_events=False
    )
    tasks: List[Task] = []
    for task in tasks_in_template:
        old_task_id = task.id
        task.id = generate_uuid()
        task.created_at = generate_timestamp()
        task.org_id = org_id
        task.project_id = project_id
        task.metadata = only_keep_fields(
            task.metadata,
            [
                "prompt_tokens",
                "completion_tokens",
                "language",
                "sentiment_label",
                "sentiment_score",
                "sentiment_magnitude",
                "user_id",
                "version_id",
            ],
        )
        if task.last_eval:
            task.last_eval.id = generate_uuid()
            task.last_eval.created_at = generate_timestamp()
            task.last_eval.project_id = project_id
            task.last_eval.org_id = org_id
            task.last_eval.task_id = task.id
            if task.last_eval.session_id:
                paired_last_eval_session = session_pairs.get(task.last_eval.session_id)
                if paired_last_eval_session:
                    task.last_eval.session_id = paired_last_eval_session.id
        if task.session_id:
            paired_session = session_pairs.get(task.session_id)
            if paired_session:
                task.session_id = paired_session.id
        task_pairs[old_task_id] = task
        tasks.append(task)

    if len(tasks) > 0:
        await mongo_db["tasks"].insert_many([task.model_dump() for task in tasks])
    else:
        raise ValueError("No tasks found in the default project")

    # Add events to the project
    default_events = (
        await mongo_db["events"]
        .find(
            {
                "project_id": template_project_id,
                "removed": {"$ne": True},
            }
        )
        .to_list(length=None)
    )

    events: List[Event] = []
    for event in default_events:
        event_model = Event.model_validate(event)
        if event_model.task_id not in task_pairs:
            logger.error(
                f"Default project has been modified, task {event_model.task_id} not found in task_pairs. Skipping event {event_model.event_name}"
            )
            continue
        event_pairs[event_model.id] = event_model
        event_model.id = generate_uuid()
        event_model.created_at = generate_timestamp()
        event_model.project_id = project_id
        event_model.org_id = org_id
        # Copy the whole task before overriding the task_id
        event_model.task = task_pairs[event_model.task_id]
        event_model.task_id = task_pairs[event_model.task_id].id
        if event_model.session_id:
            paired_session = session_pairs.get(event_model.session_id)
            if paired_session:
                event_model.session_id = paired_session.id
        if event_model.event_definition:
            paired_event_definition = event_definition_pairs.get(
                event_model.event_definition.id
            )
            if paired_event_definition:
                event_model.event_definition = paired_event_definition

        # Don't add the event if it's a duplicate
        if event_model.event_name not in [
            event.event_name for event in events if event.task_id == event_model.task_id
        ]:
            events.append(event_model)

    if len(events) > 0:
        await mongo_db["events"].insert_many([event.model_dump() for event in events])
    else:
        raise ValueError("No events found in the default project")

    # Import the clusterings, the clusters and the embeddings from the target project

    embeddings_in_template = (
        await mongo_db["private-embeddings"]
        .find({"project_id": template_project_id})
        .to_list(length=None)
    )
    embeddings: List[Embedding] = []
    for embedding in embeddings_in_template:
        embedding_model = Embedding.model_validate(embedding)
        old_embedding_id = embedding_model.id
        embedding_model.id = generate_uuid()
        embedding_model.project_id = project_id
        embedding_model.org_id = org_id
        if embedding_model.session_id:
            paired_session = session_pairs.get(embedding_model.session_id)
            if paired_session:
                embedding_model.session_id = paired_session.id
        if embedding_model.task_id:
            paired_task = task_pairs.get(embedding_model.task_id)
            if paired_task:
                embedding_model.task_id = paired_task.id
        embeddings.append(embedding_model)
        embedding_pairs[old_embedding_id] = embedding_model

    if len(embeddings) > 0:
        await mongo_db["private-embeddings"].insert_many(
            [embedding.model_dump() for embedding in embeddings]
        )
    else:
        logger.error(
            f"No embeddings found in the template project {template_project_id}"
        )

    default_clusters = (
        await mongo_db["private-clusters"]
        .find({"project_id": template_project_id})
        .to_list(length=None)
    )

    clusters: List[Cluster] = []
    for cluster in default_clusters:
        cluster_model = Cluster.model_validate(cluster)
        old_cluster_id = cluster_model.id
        cluster_model.id = generate_uuid()
        cluster_model.project_id = project_id
        cluster_model.org_id = org_id
        if cluster_model.sessions_ids:
            for i, session_id in enumerate(cluster_model.sessions_ids):
                cluster_model.sessions_ids[i] = session_pairs[session_id].id
        if cluster_model.tasks_ids:
            for i, task_id in enumerate(cluster_model.tasks_ids):
                cluster_model.tasks_ids[i] = task_pairs[task_id].id
        clusters.append(cluster_model)
        cluster_pairs[old_cluster_id] = cluster_model

    clusterings_in_template = (
        await mongo_db["private-clusterings"]
        .find({"project_id": template_project_id})
        .to_list(length=None)
    )
    clusterings: List[Clustering] = []
    for clustering in clusterings_in_template:
        clustering_model = Clustering.model_validate(clustering)
        old_clustering_id = clustering_model.id
        clustering_model.id = generate_uuid()
        clustering_model.project_id = project_id
        clustering_model.org_id = org_id

        for i, cluster_id in enumerate(clustering_model.clusters_ids):
            clustering_model.clusters_ids[i] = cluster_pairs[cluster_id].id
        if clustering_model.pca is not None:
            for i, cluster_id in enumerate(
                clustering_model.pca.get("clusters_ids", [])
            ):
                clustering_model.pca["clusters_ids"][i] = cluster_pairs[cluster_id].id
            for i, embedding_id in enumerate(
                clustering_model.pca.get("embeddings_ids", [])
            ):
                clustering_model.pca["embeddings_ids"][i] = embedding_pairs[
                    embedding_id
                ].id

        clusterings.append(clustering_model)
        clustering_pairs[old_clustering_id] = clustering_model

    for cluster in clusters:
        cluster.clustering_id = clustering_pairs[cluster.clustering_id].id

    if len(clusterings) > 0:
        await mongo_db["private-clusterings"].insert_many(
            [clustering.model_dump() for clustering in clusterings]
        )
        if len(clusters) > 0:
            await mongo_db["private-clusters"].insert_many(
                [cluster.model_dump() for cluster in clusters]
            )
        else:
            logger.warning(
                f"No clusters found in the template project {template_project_id}"
            )
    else:
        logger.warning(
            f"No clusterings found in the template project {template_project_id}"
        )

    logger.debug(
        f"Populated project {project_id} with event definitions {event_definition_pairs}"
    )
    return None
