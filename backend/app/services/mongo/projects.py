import datetime
import io
import time
from typing import Dict, List, Optional, Tuple, Union

from app.api.platform.models.explore import Sorting
from app.services.mongo.sessions import compute_session_length
import pandas as pd
import resend
from app.api.platform.models import UserMetadata, Pagination
from app.core import config
from app.db.models import (
    Event,
    EventDefinition,
    Project,
    Session,
    Task,
    Test,
    ProjectDataFilters,
)
from app.db.mongo import get_mongo_db
from app.security.authentification import propelauth
from app.services.mongo.metadata import fetch_user_metadata
from app.services.mongo.jobs import create_job
from app.services.slack import slack_notification
from app.utils import generate_timestamp
from fastapi import HTTPException
from loguru import logger
from openai import AsyncOpenAI
from propelauth_fastapi import User

import phospho
from phospho.utils import filter_nonjsonable_keys


def cast_datetime_or_timestamp_to_timestamp(
    date_or_ts: Union[datetime.datetime, int],
) -> int:
    if isinstance(date_or_ts, datetime.datetime):
        return int(date_or_ts.timestamp())
    else:
        return date_or_ts


async def get_project_by_id(project_id: str) -> Project:
    mongo_db = await get_mongo_db()

    # doc = db.get_document("projects", project_id).get()
    project_data = await mongo_db["projects"].find_one({"id": project_id})

    if project_data is None:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    # Handle different names of the same field
    if "creation_date" in project_data.keys():
        project_data["created_at"] = project_data["creation_date"]

    if "id" not in project_data.keys():
        project_data["id"] = project_data["_id"]

    if "org_id" not in project_data.keys():
        raise HTTPException(
            status_code=500,
            detail="Project has no org_id. Please reach out to the Phospho team contact@phospho.app",
        )

    # If event_name not in project_data.settings.events.values(), add it based on the key
    if (
        "settings" in project_data.keys()
        and "events" in project_data["settings"].keys()
    ):
        for event_name, event in project_data["settings"]["events"].items():
            if "event_name" not in event.keys():
                project_data["settings"]["events"][event_name][
                    "event_name"
                ] = event_name
                mongo_db["projects"].update_one(
                    {"_id": project_data["_id"]},
                    {"$set": {"settings.events": project_data["settings"]["events"]}},
                )

    try:
        project = Project.model_validate(project_data)
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

    if payload:
        # Check if there is some events in the payload without a job_id
        if "settings" in payload.keys() and "events" in payload["settings"].keys():
            for event_name, event in payload["settings"]["events"].items():
                logger.debug(f"Event: {event}")
                if "job_id" not in event.keys():
                    # Create the corresponding jobs based on the project settings
                    job = await create_job(
                        org_id=project.org_id,
                        project_id=project.id,
                        job_type="event_detection",
                        parameters=event,
                    )
                    # Update the settings with the job_id
                    payload["settings"]["events"][event_name]["job_id"] = job.id

        logger.debug(f"Update project {project.id} with payload {payload}")

        # Update the database
        update_result = await mongo_db["projects"].update_one(
            {"id": project.id}, {"$set": payload}
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
    updated_project = await get_project_by_id(project_id)
    logger.debug(f"Updated project: {updated_project} {updated_project.settings}")
    return updated_project


async def get_all_tasks(
    project_id: str,
    flag_filter: Optional[str] = None,
    metadata_filter: Optional[Dict[str, object]] = None,
    last_eval_source_filter: Optional[str] = None,
    event_name_filter: Optional[List[str]] = None,
    created_at_start: Optional[Union[int, datetime.datetime]] = None,
    created_at_end: Optional[Union[int, datetime.datetime]] = None,
    get_events: bool = True,
    get_tests: bool = False,
    validate_metadata: bool = False,
    limit: Optional[int] = None,
    pagination: Optional[Pagination] = None,
    sorting: Optional[List[Sorting]] = None,
) -> List[Task]:
    """
    Get all the tasks of a project.

    limit: Set to None to get all tasks
    get_tests:
    """

    mongo_db = await get_mongo_db()

    main_filter: Dict[str, object] = {}
    main_filter["project_id"] = project_id
    if flag_filter:
        main_filter["flag"] = flag_filter
    if last_eval_source_filter:
        main_filter["last_eval.source"] = last_eval_source_filter
    if metadata_filter:
        main_filter["metadata"] = metadata_filter
    if created_at_start:
        main_filter["created_at"] = {
            "$gte": cast_datetime_or_timestamp_to_timestamp(created_at_start)
        }
    if created_at_end:
        main_filter["created_at"] = {
            **main_filter.get("created_at", {}),
            "$lte": cast_datetime_or_timestamp_to_timestamp(created_at_end),
        }
    if not get_tests:
        main_filter["test_id"] = None

    pipeline: List[Dict[str, object]] = [
        {"$match": main_filter},
    ]
    if event_name_filter is not None:
        pipeline.append({"$match": {"events.event_name": {"$in": event_name_filter}}})

    if sorting is not None and len(sorting) > 0:
        sorting_dict = {sort.id: 1 if sort.desc else -1 for sort in sorting}
        pipeline.append({"$sort": sorting_dict})
    else:
        pipeline.append({"$sort": {"created_at": -1}})

    # Add pagination
    if pagination:
        pipeline.extend(
            [
                {"$skip": pagination.page * pagination.per_page},
                {"$limit": pagination.per_page},
            ]
        )
        limit = None

    # Deduplicate events names. We want the unique event_names of the task
    pipeline.append(
        {
            "$addFields": {
                "events": {
                    "$reduce": {
                        "input": "$events",
                        "initialValue": [],
                        "in": {
                            "$concatArrays": [
                                "$$value",
                                {
                                    "$cond": [
                                        {
                                            "$in": [
                                                "$$this.event_name",
                                                "$$value.event_name",
                                            ]
                                        },
                                        [],
                                        ["$$this"],
                                    ]
                                },
                            ]
                        },
                    }
                }
            }
        },
    )

    tasks = await mongo_db["tasks"].aggregate(pipeline).to_list(length=limit)

    # Cast to tasks
    valid_tasks = [Task.model_validate(data) for data in tasks]

    if validate_metadata:
        for task in valid_tasks:
            # Remove the _id field from the task metadata
            if task.metadata is not None:
                task.metadata = filter_nonjsonable_keys(task.metadata)

    return valid_tasks


async def email_project_tasks(
    project_id: str,
    uid: str,
    limit: Optional[int] = 1000,
):
    if config.ENVIRONMENT != "preview":
        tasks_list = await get_all_tasks(project_id=project_id)

        # Get the user email
        user = propelauth.fetch_user_metadata_by_user_id(uid, include_orgs=False)

        # Use Resend to send the email
        resend.api_key = config.RESEND_API_KEY

        try:
            # Convert task list to Pandas DataFrame
            df = pd.DataFrame([task.model_dump() for task in tasks_list])

            # Convert the DataFrame to a CSV string, then to bytes
            csv_string = df.to_csv(index=False)
            csv_bytes = csv_string.encode()

            # Get the excel file buffer
            excel_buffer = io.BytesIO()
            df.to_excel(excel_buffer, index=False)
            excel_data = excel_buffer.getvalue()
            # encoded_excel = base64.b64encode(excel_data).decode()

            params = {
                "from": "phospho <contact@phospho.ai>",
                "to": [user.get("email")],
                "subject": "Your exported tasks are ready",
                "html": f"""<p>Hello!<br><br>Here are attached your exported tasks for the project with id {project_id} (timestamp: {datetime.datetime.now().isoformat()})</p>
                <p><br>So, what do you think about phospho for now? Feel free to respond to this email address and share your toughts !</p>
                <p>Enjoy,<br>
                The Phospho Team</p>
                """,
                "attachments": [
                    {
                        "filename": "tasks.csv",
                        "content": list(csv_bytes),  # Attach the bytes content directly
                    },
                    {
                        "filename": "tasks.xlsx",
                        "content": list(
                            excel_data
                        ),  # Attach the bytes content directly for Excel
                    },
                ],
            }

            email = resend.Emails.send(params)

            logger.info(f"Successfully sent tasks by email to {user.get('email')}")

        except Exception as e:
            logger.error(f"Error sending tasks by email: {e}")

            # Send an error message to the user
            params = {
                "from": "phospho <contact@phospho.ai>",
                "to": [user.get("email")],
                "subject": "Error exporting your tasks",
                "html": f"""<p>Hello!<br><br>We could not export your tasks for the project with id {project_id} (timestamp: {datetime.datetime.now().isoformat()})</p>
                <p><br>Please contact the support at contact@phospho.app</p>
                <p>Best,<br>
                The Phospho Team</p>
                """,
            }

            email = resend.Emails.send(params)

            logger.debug("Sent error message to user")

    else:
        logger.warning("Preview environment: emails disabled")


async def get_all_events(
    project_id: str,
    limit: Optional[int] = None,
    events_filter: Optional[ProjectDataFilters] = None,
    include_removed: bool = False,
    unique: bool = False,
) -> List[Event]:
    mongo_db = await get_mongo_db()
    additional_event_filters: Dict[str, object] = {}
    pipeline: List[Dict[str, object]] = []
    if events_filter is not None:
        if events_filter.event_name is not None:
            if isinstance(events_filter.event_name, str):
                additional_event_filters["event_name"] = events_filter.event_name
            if isinstance(events_filter.event_name, list):
                additional_event_filters["event_name"] = {
                    "$in": events_filter.event_name
                }
        if events_filter.created_at_start is not None:
            additional_event_filters["created_at"] = {
                "$gt": cast_datetime_or_timestamp_to_timestamp(
                    events_filter.created_at_start
                )
            }
        if events_filter.created_at_end is not None:
            additional_event_filters["created_at"] = {
                **additional_event_filters.get("created_at", {}),
                "$lt": cast_datetime_or_timestamp_to_timestamp(
                    events_filter.created_at_end
                ),
            }
    if not include_removed:
        additional_event_filters["removed"] = {"$ne": True}

    pipeline.append(
        {
            "$match": {
                "project_id": project_id,
                **additional_event_filters,
            }
        }
    )

    if unique:
        # Deduplicate the events based on event name
        pipeline.extend(
            [
                {
                    "$group": {
                        "_id": "$event_name",
                        "doc": {"$first": "$$ROOT"},
                    }
                },
                {"$replaceRoot": {"newRoot": "$doc"}},
            ]
        )

    pipeline.append({"$sort": {"created_at": -1}})

    events = await mongo_db["events"].aggregate(pipeline).to_list(length=limit)

    # Cast to model
    events = [Event.model_validate(data) for data in events]
    return events


async def get_all_sessions(
    project_id: str,
    limit: int = 1000,
    sessions_filter: Optional[ProjectDataFilters] = None,
    get_events: bool = True,
    get_tasks: bool = False,
    pagination: Optional[Pagination] = None,
    sorting: Optional[List[Sorting]] = None,
) -> List[Session]:
    mongo_db = await get_mongo_db()
    # await compute_session_length(project_id)
    additional_sessions_filter: Dict[str, object] = {}
    if sessions_filter is not None:
        if sessions_filter.created_at_start is not None:
            additional_sessions_filter["created_at"] = {
                "$gte": cast_datetime_or_timestamp_to_timestamp(
                    sessions_filter.created_at_start
                )
            }
        if sessions_filter.created_at_end is not None:
            additional_sessions_filter["created_at"] = {
                **additional_sessions_filter.get("created_at", {}),
                "$lte": sessions_filter.created_at_end,
            }
        if sessions_filter.event_name is not None:
            additional_sessions_filter["events.event_name"] = {
                "$in": sessions_filter.event_name
            }
        if sessions_filter.flag is not None:
            additional_sessions_filter["flag"] = sessions_filter.flag

    pipeline = [
        {
            "$match": {
                "project_id": project_id,
                **additional_sessions_filter,
            }
        },
    ]
    if get_events:
        pipeline.extend(
            [
                {
                    "$lookup": {
                        "from": "events",
                        "localField": "id",
                        "foreignField": "session_id",
                        "as": "events",
                    }
                },
                {"$match": {"events.removed": {"$ne": True}}},
            ]
        )
    if get_tasks or (
        sessions_filter is not None and sessions_filter.user_id is not None
    ):
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
        if sessions_filter is not None and sessions_filter.user_id is not None:
            logger.debug(f"Filtering sessions by user_id: {sessions_filter.user_id}")
            pipeline.extend(
                [
                    {
                        "$match": {
                            # Filter the sessions to keep the ones where a tasks.metadata.user_id matches the filter
                            "tasks.metadata.user_id": sessions_filter.user_id
                        }
                    },
                ]
            )

    if sorting is not None and len(sorting) > 0:
        sorting_dict = {sort.id: 1 if sort.desc else -1 for sort in sorting}
        pipeline.append({"$sort": sorting_dict})
    else:
        pipeline.append({"$sort": {"created_at": -1}})

    # Add pagination
    if pagination:
        pipeline.extend(
            [
                {"$skip": pagination.page * pagination.per_page},
                {"$limit": pagination.per_page},
            ]
        )

    if get_events:
        pipeline.extend(
            [
                # If events is None, set to empty list
                {"$addFields": {"events": {"$ifNull": ["$events", []]}}},
                # Deduplicate events names. We want the unique event_names of the session
                {
                    "$addFields": {
                        "events": {
                            "$reduce": {
                                "input": "$events",
                                "initialValue": [],
                                "in": {
                                    "$concatArrays": [
                                        "$$value",
                                        {
                                            "$cond": [
                                                {
                                                    "$in": [
                                                        "$$this.event_name",
                                                        "$$value.event_name",
                                                    ]
                                                },
                                                [],
                                                ["$$this"],
                                            ]
                                        },
                                    ]
                                },
                            }
                        }
                    }
                },
            ]
        )

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


async def generate_events_for_use_case(
    project_id: str,
    build: str,
    purpose: str,
    custom_build: Optional[str] = None,
    custom_purpose: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Tuple[List[EventDefinition], Optional[str]]:
    mongo_db = await get_mongo_db()

    start_time = time.time()
    build_to_desc = {
        "knowledge-assistant": "A knowledge assistant that helps users find information. He must be accurate, truthful and fast.",
        "virtual-companion": "A virtual companion that helps users feel less lonely. He must be empathic, friendly, and engaging.",
        "narrator": "A narrator that tells stories to users. He must be engaging, fun, and entertaining.",
        "ask-ai": "A feature that allows to quickly give an AI answer to a user's question. The assistant must be fast, accurate, and to the point.",
        "customer-support": "A customer support assistant that helps users with their issues about an opened ticket. The assistant must be professional, empathic, patient, and helpful.",
    }
    if custom_build is not None:
        build_full_description = custom_build
    else:
        if build in build_to_desc.keys() and build != "other":
            build_full_description = build_to_desc[build]
        else:
            build_full_description = list(build_to_desc.values())[0]

    purpose_to_desc = {
        "entertainment": "A good assistant must be fun, engaging and entertaining."
        + " A successful interaction is when the user is having fun, laughing, and enjoying the experience.",
        "aquisition": "A good assistant qualifies customer leads for a company."
        + " The assistant must be engaging, open-minded, and listen to the issues of the user. Interesting users are those who are genuinely interested in the product or service.",
        "retention": "A good assistant is persuasive, empathic, friendly, and to the point."
        + " A successful interaction is when the user is convinced to stay, to buy, or to come back.",
        "marketing": "A good assistant is truthful to the brand, engaging, and persuasive."
        + "A good assistant doesn't hallucinate or make up prices.",
        "productivity": "A good assistant is accurate and to the point. His answers benefits the user. The user learns something and gets more efficient."
        + "The assistant's Answers are short and precise. The assistant must be able to understand the user's request and provide the right information."
        + "The user is thanking the assistant for the help. The assistant doesn't hallucinate.",
        "resolve-tikets": "A good assistant is professional, empathic, patient, and helpful. He's precise and always correct."
        + "The assistant must be certain that he understands the user's request and provide the proper information without damaging the brand.",
    }
    if custom_purpose is not None:
        purpose_full_description = custom_purpose
    else:
        if purpose in purpose_to_desc.keys() and purpose != "other":
            purpose_full_description = purpose_to_desc[purpose]
        else:
            purpose_full_description = list(purpose_to_desc.values())[0]

    # Format the description without the line breaks
    build_full_description = " ".join(build_full_description.split())
    purpose_full_description = " ".join(purpose_full_description.split())

    logger.info(f"build_full_description: {build_full_description}")
    logger.info(f"purpose_full_description: {purpose_full_description}")

    # Create a prompt
    openai_client = AsyncOpenAI()
    system_prompt = "You are a talented, sharp, and exceptionally inspiring product manager at a company that is building a new AI assistant. Don't talk, just go."
    prompt = f"""You are thinking about the events occurring in a conversation that are relevant to monitor to assess \
the AI assistant's alignment and the user's satisfaction. You also want to detect the \
shortcommings or hiccups in the conversation. \

Provide a list of 3 to 5 relevant events that should be monitored in the conversation.\
Use the following template.
- event name: description

---

Example:
Assistant description: (knowledge-assistant) A knowledge assistant that helps users find information. He must be accurate, truthful and fast.
Use case: (entertainment) A good assistant must be fun, engaging and entertaining. A successful interaction is when the user is having fun, laughing, and enjoying the experience.

Relevant events:
- user laughing: The user is laughing during the interaction with the assistant.
- inaccurate answer: The assistant provides an inaccurate answer to the user's question. The user points out an inaccuracy in the assistant's answer.
- unable to answer: The user asked a question that the assistant is unable to answer. The assistant says "I don't know", "I can't answer you", or "I don't have the information".
- user thanks: The user is thanking the assistant for the help. The assistant doesn't hallucinate.

---

Assistant description: ({build}) {build_full_description}
Use case: ({purpose}) {purpose_full_description}

Relevant events:
"""

    # Get the response from the API
    try:
        response = await openai_client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {"role": "user", "content": prompt},
            ],
            max_tokens=500,
            model="gpt-3.5-turbo",
            temperature=0.2,
        )
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        response = None

    if response is None or response.choices[0].message.content is None:
        # Return the default events if error
        default_events = {
            "question_answering": {
                "description": "The user asks a question to the assistant.",
                "webhook": None,
            },
            "thanks": {
                "description": "The user thanks the assistant.",
                "webhook": None,
            },
            "toxic_behavior": {
                "description": "The assistant is being toxic to the user.",
                "webhook": None,
            },
        }
        return (
            [
                EventDefinition(
                    event_name=k,
                    description=v.get("description", "Default description"),
                    webhook=v["webhook"],
                )
                for k, v in default_events.items()
            ],
            {},  # Empty logged content
        )
    # Extract the events from the response
    extracted_events = response.choices[0].message.content.split("\n")[1:]
    extracted_events = [event.strip() for event in extracted_events if event.strip()]
    # Extract the event name and description
    events = []
    for event in extracted_events:
        event_name, description = event.split(":")
        event_name = event_name.strip()
        # Remove "- " at the beginning of event_name
        if event_name.startswith("-"):
            event_name = event_name[1:]
        event_name = event_name.strip()
        description = description.strip()
        try:
            events.append(
                EventDefinition(event_name=event_name, description=description)
            )
        except Exception as e:
            logger.warning(f"Error creating event: {e}. Skipping.")

    execution_time = time.time() - start_time

    # Log to phospho
    if config.ENVIRONMENT != "preview":
        logged_content = phospho.log(
            input=prompt,
            output=extracted_events,
            system_prompt=system_prompt,
            temperature=0.2,
            execution_time=execution_time,
            build=build,
            purpose=purpose,
            model="gpt-3.5-turbo",
            user_id=user_id,
        )
        logger.info(f"Logged content: {logged_content}")
    else:
        logged_content = {}
    return events, logged_content


async def suggest_events_for_use_case(
    project_id: str,
    build: str,
    purpose: str,
    custom_build: Optional[str] = None,
    custom_purpose: Optional[str] = None,
    user_id: Optional[str] = None,
) -> Tuple[List[EventDefinition], Optional[str]]:
    mongo_db = await get_mongo_db()

    # See if there already suggestions for this build and purpose
    if build != "other" and purpose != "other":
        existing_suggestions = await mongo_db["suggested_events"].find_one(
            {"build": build, "purpose": purpose}, sort=[("created_at", -1)]
        )
        if existing_suggestions:
            logger.info("Found existing suggestions. Returning them.")
            existing_events = [
                EventDefinition(
                    event_name=event["event_name"],
                    description=event["description"],
                    webhook=event["webhook"],
                )
                for event in existing_suggestions["suggested_events"]
            ]
            if config.ENVIRONMENT != "preview":
                logged_content = phospho.log(
                    input=f"Build: {build}, Purpose: {purpose}",
                    output=existing_suggestions["suggested_events"],
                    execution_time=0,
                    build=build,
                    purpose=purpose,
                    user_id=user_id,
                )
                task_id: str = logged_content.get("task_id", None)
            else:
                logged_content = {}
                task_id = None
            return existing_events, task_id

    # Otherwise, generate the events
    events, logged_content = await generate_events_for_use_case(
        project_id=project_id,
        build=build,
        purpose=purpose,
        custom_build=custom_build,
        custom_purpose=custom_purpose,
        user_id=user_id,
    )

    # Store the suggestions
    mongo_db["suggested_events"].insert_one(
        {
            "project_id": project_id,
            "created_at": generate_timestamp(),
            "build": build,
            "purpose": purpose,
            "suggested_events": [event.model_dump() for event in events],
        }
    )

    return events, logged_content.get("task_id", None)


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
