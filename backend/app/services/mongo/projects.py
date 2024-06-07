import datetime
import io
from typing import Dict, List, Optional, Union

import pandas as pd
import resend
from app.api.platform.models import Pagination, UserMetadata
from app.api.platform.models.explore import Sorting
from app.core import config
from app.db.models import (
    EventDefinition,
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
from app.services.mongo.extractor import run_recipe_on_tasks
from app.services.mongo.metadata import fetch_user_metadata
from app.services.mongo.tasks import (
    get_all_tasks,
    label_sentiment_analysis,
)
from app.services.mongo.events import get_all_events
from app.services.slack import slack_notification
from app.utils import (
    cast_datetime_or_timestamp_to_timestamp,
    generate_timestamp,
    generate_uuid,
)
from fastapi import HTTPException
from loguru import logger
from propelauth_fastapi import User

from phospho.models import Threshold


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
        if project.model_dump() != project_data:
            mongo_db["projects"].update_one(
                {"_id": project_data["_id"]}, {"$set": project.model_dump()}
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
                    logger.error(f"Error disabling recipe for event {event_name}: {e}")
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
        _ = await mongo_db["projects"].update_one(
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
    await mongo_db["event_definitions"].insert_many(
        [event.model_dump() for event in events]
    )
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

        email = resend.Emails.send(params)
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
            "subject": "Your exported tasks are ready",
            "html": f"""<p>Hello!<br><br>Here are attached your exported tasks for the project with id {project_id} (timestamp: {datetime.datetime.now().isoformat()})</p>
            <p><br>So, what do you think about phospho for now? Feel free to respond to this email address and share your toughts !</p>
            <p>Enjoy,<br>
            The Phospho Team</p>
            """,
            "attachments": exports,
        }

        try:
            resend.Emails.send(params)
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
    collection_name = "sessions"
    # await compute_session_length(project_id)
    additional_sessions_filter: Dict[str, object] = {}
    if filters is not None:
        if filters.created_at_start is not None:
            additional_sessions_filter["created_at"] = {
                "$gte": cast_datetime_or_timestamp_to_timestamp(
                    filters.created_at_start
                )
            }
        if filters.created_at_end is not None:
            additional_sessions_filter["created_at"] = {
                **additional_sessions_filter.get("created_at", {}),
                "$lte": filters.created_at_end,
            }

        if filters.flag is not None:
            additional_sessions_filter["flag"] = filters.flag

        if filters.metadata is not None:
            for key, value in filters.metadata.items():
                additional_sessions_filter[f"metadata.{key}"] = value

    pipeline: List[Dict[str, object]] = [
        {
            "$match": {
                "project_id": project_id,
                **additional_sessions_filter,
            }
        },
    ]
    if get_events or (filters is not None and filters.event_name is not None):
        collection_name = "sessions_with_events"
        if filters is not None and filters.event_name is not None:
            pipeline.extend(
                [
                    {
                        "$match": {
                            "$and": [
                                {"events": {"$ne": []}},
                                {
                                    "events": {
                                        "$elemMatch": {
                                            "event_name": {"$in": filters.event_name}
                                        }
                                    }
                                },
                            ]
                        },
                    },
                ]
            )

    if get_tasks or (filters is not None and filters.user_id is not None):
        pipeline.extend(
            [
                {
                    "$lookup": {
                        "from": "tasks",
                        "localField": "id",
                        "foreignField": "session_id",
                        "as": "tasks",
                    }
                },
                # If tasks is None, set to empty list
                {"$addFields": {"tasks": {"$ifNull": ["$tasks", []]}}},
            ]
        )
        if filters is not None and filters.user_id is not None:
            logger.debug(f"Filtering sessions by user_id: {filters.user_id}")
            pipeline.extend(
                [
                    {
                        "$match": {
                            # Filter the sessions to keep the ones where a tasks.metadata.user_id matches the filter
                            "tasks.metadata.user_id": filters.user_id
                        }
                    },
                ]
            )

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
                    "from": "sessions_with_events",
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

    sessions = await mongo_db[collection_name].aggregate(pipeline).to_list(length=limit)

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


async def store_onboarding_survey(project_id: str, user: User, survey: dict):
    mongo_db = await get_mongo_db()
    project = await get_project_by_id(project_id)
    doc = {
        "project_id": project_id,
        "project": project.model_dump(),
        "user_id": user.user_id,
        "created_at": generate_timestamp(),
        "survey": survey,
    }
    mongo_db["onboarding_surveys"].insert_one(doc)
    await slack_notification(
        f"New onboarding survey from {user.email} for project {project.project_name} {project_id}: {survey}"
    )
    return


async def get_all_users_metadata(project_id: str) -> List[UserMetadata]:
    """
    Get metadata about the end-users of a project

    Groups the tasks by user_id and return a list of UserMetadata.
    Every UserMetadata contains:
        user_id: str
        nb_tasks: int
        avg_success_rate: float
        avg_session_length: float
        events: List[Event]
        tasks: List[Task]
        sessions: List[Session]
    """
    try:
        users = await fetch_user_metadata(project_id=project_id, user_id=None)
    except Exception as e:
        logger.error(f"Error fetching users metadata: {e}")
        users = []
    return users


async def backcompute_recipe(job_id: str, tasks: List[Task]) -> None:
    """
    Run predictions for a job on all the tasks of a project that have not been processed yet.
    """
    mongo_db = await get_mongo_db()

    recipe = await mongo_db["recipes"].find_one({"id": job_id})
    recipe = Recipe.model_validate(recipe)

    # For each task, check if a prediction has a job_id and a task_id matching the task
    tasks_to_process = []

    for task in tasks:
        prediction = await mongo_db["job_results"].find_one(
            {"task_id": task.id, "job_metadata.recipe_id": recipe.id}
        )
        if prediction is None:
            tasks_to_process.append(task)

    # Send the task to the job pipeline of the extractor
    await run_recipe_on_tasks(
        tasks=tasks_to_process, recipe=recipe, org_id=recipe.org_id
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


async def populate_default(
    project_id: str,
    org_id: str,
) -> None:
    """
    Populate the project with default values
    """
    logger.info(f"Populating project {project_id} with default values")
    mongo_db = await get_mongo_db()

    if config.ENVIRONMENT == "production":
        target_project_id = "6a6323d1447a44ddac2dae42d7c39749"
    else:
        target_project_id = "5383b5ce54314a76a9bb1774839e8417"

    target_project = await get_project_by_id(target_project_id)
    target_project.org_id = org_id
    target_project.id = project_id
    await update_project(target_project)

    # Add tasks to the project
    default_tasks = await get_all_tasks(target_project_id)
    tasks = []
    for task in default_tasks:
        task.id = generate_uuid()
        task.created_at = generate_timestamp()
        task.project_id = project_id
        task.org_id = org_id
        tasks.append(task)
    await mongo_db["tasks"].insert_many([task.model_dump() for task in tasks])

    # Add sessions to the project
    default_sessions = await get_all_sessions(target_project_id)
    sessions = []
    for session in default_sessions:
        session.id = generate_uuid()
        session.created_at = generate_timestamp()
        session.project_id = project_id
        session.org_id = org_id
        sessions.append(session)
    await mongo_db["sessions"].insert_many(
        [session.model_dump() for session in sessions]
    )

    return None
