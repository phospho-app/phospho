from typing import Dict, List, Literal, Optional, Tuple, cast

from app.db.models import Event, EventDefinition, Project, Session, Task
from app.db.mongo import get_mongo_db
from app.services.mongo.tasks import task_filtering_pipeline_match
from fastapi import HTTPException
from loguru import logger
import datetime

from phospho.models import ProjectDataFilters, ScoreRange
from phospho.utils import is_jsonable


async def create_session(
    project_id: str, org_id: str, data: Optional[dict] = None
) -> Session:
    """
    Create a new session
    """
    mongo_db = await get_mongo_db()
    new_session = Session(project_id=project_id, org_id=org_id, data=data)
    mongo_db["sessions"].insert_one(new_session.model_dump())
    return new_session


async def get_session_by_id(session_id: str) -> Session:
    mongo_db = await get_mongo_db()
    # session = await mongo_db["sessions"].find_one({"id": session_id})
    # Merge events from the session
    found_session = (
        await mongo_db["sessions_with_events"]
        .find(
            {"id": session_id},
        )
        .to_list(length=1)
    )
    session = found_session[0] if found_session else None

    if session is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    try:
        session_model = Session.model_validate(session)
    except Exception as e:
        logger.warning(f"Error validating model of session {session_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error validating model of session {session_id}: {e}",
        )
    return session_model


async def fetch_session_tasks(session_id: str, limit: int = 1000) -> List[Task]:
    """
    Fetch all tasks for a given session id.
    """
    mongo_db = await get_mongo_db()
    tasks = (
        await mongo_db["tasks_with_events"]
        .find({"session_id": session_id})
        .sort("created_at", -1)
        .to_list(length=limit)
    )
    tasks = [Task.model_validate(data) for data in tasks]
    return tasks


async def format_session_transcript(session: Session) -> str:
    """
    Format the transcript of a session into a human-readable string.

    Eg:
    User: Hello
    Assistant: Hi there!
    """

    tasks = await fetch_session_tasks(session.id)

    transcript = ""
    for task in tasks:
        transcript += f"User: {task.input}\n"
        transcript += f"Assistant: {task.output}\n"

    return transcript


async def edit_session_metadata(session_data: Session, **kwargs) -> Session:
    """
    Updates the metadata of a session.
    """
    mongo_db = await get_mongo_db()
    for key, value in kwargs.items():
        if value is not None:
            if key in Session.model_fields.keys() and is_jsonable(value):
                setattr(session_data, key, value)
            else:
                logger.warning(
                    f"Cannot update Session.{key} to {value} (field not in schema)"
                )
    _ = await mongo_db["sessions"].update_one(
        {"id": session_data.id}, {"$set": session_data.model_dump()}
    )
    updated_session = await get_session_by_id(session_data.id)
    return updated_session


async def compute_session_length(project_id: str):
    """
    Executes an aggregation pipeline to compute the length of each session for a given project.

    This can be made smarter by:
    1. Storing the latest update time of a session
    2. Fetching the session_id in the tasks collection that were created_at after the latest update time
    3. Updating the session length only for those sessions
    """
    mongo_db = await get_mongo_db()
    session_pipeline = [
        {"$match": {"project_id": project_id}},
        {
            "$lookup": {
                "from": "tasks",
                "localField": "id",
                "foreignField": "session_id",
                "as": "tasks",
            }
        },
        {
            "$match": {
                "$and": [
                    {"tasks": {"$ne": None}},
                    {"tasks": {"$ne": []}},
                ]
            }
        },
        {"$set": {"session_length": {"$size": "$tasks"}}},
        {"$unset": "tasks"},
        {
            "$merge": {
                "into": "sessions",
                "on": "_id",
                "whenMatched": "merge",
                "whenNotMatched": "discard",
            }
        },
    ]

    await mongo_db["sessions"].aggregate(session_pipeline).to_list(length=None)


async def compute_task_position(
    project_id: str, filters: Optional[ProjectDataFilters] = None
):
    """
    Executes an aggregation pipeline to compute the task position for each task.
    """
    mongo_db = await get_mongo_db()

    if filters is None:
        filters = ProjectDataFilters()

    main_filter: Dict[str, object] = {"project_id": project_id}
    if filters.created_at_start is not None:
        main_filter["created_at"] = {"$gte": filters.created_at_start}
    if filters.created_at_end is not None:
        main_filter["created_at"] = {
            **main_filter.get("created_at", {}),
            "$lte": filters.created_at_end,
        }

    tasks_filter, task_collection = await task_filtering_pipeline_match(
        project_id=project_id, filters=filters, collection="tasks", prefix="tasks"
    )
    pipeline = [
        {"$match": main_filter},
        {
            "$lookup": {
                "from": task_collection,
                "localField": "id",
                "foreignField": "session_id",
                "as": "tasks",
            }
        },
        {"$match": tasks_filter},
        {
            "$set": {
                "tasks": {
                    "$sortArray": {
                        "input": "$tasks",
                        "sortBy": {"tasks.created_at": 1},
                    },
                }
            }
        },
        # Transform to get 1 doc = 1 task. We also add the task position.
        {"$unwind": {"path": "$tasks", "includeArrayIndex": "task_position"}},
        # Set "is_last_task" to True for the task where task_position is == session.session_length - 1
        {
            "$set": {
                "tasks.is_last_task": {
                    "$eq": ["$task_position", {"$subtract": ["$session_length", 1]}]
                }
            }
        },
        {
            "$project": {
                "id": "$tasks.id",
                "task_position": {"$add": ["$task_position", 1]},
                "is_last_task": "$tasks.is_last_task",
                "_id": 0,
            }
        },
        {
            "$merge": {
                "into": "tasks",
                "on": "id",
                "whenMatched": "merge",
                "whenNotMatched": "discard",
            }
        },
    ]

    await mongo_db["sessions"].aggregate(pipeline).to_list(length=None)


async def get_project_id_from_session(session_id: str) -> str:
    """
    Fetches the project_id from a session_id.
    """
    mongo_db = await get_mongo_db()
    session = await mongo_db["sessions"].find_one({"id": session_id})
    if session is None:
        raise HTTPException(status_code=404, detail=f"Session {session_id} not found")
    return session["project_id"]


async def get_event_descriptions(project_id: str) -> List[str]:
    """
    Fetches the event descriptions for a given session.
    """

    mongo_db = await get_mongo_db()
    project = await mongo_db["projects"].find_one({"id": project_id})
    project_items = Project.model_validate(project)

    event_descriptions = []
    for _, event in project_items.settings.events.items():
        event_descriptions.append(event.description)

    return event_descriptions


async def event_suggestion(
    session_id: str,
    model: str = "openai:gpt-4o",
) -> list[str]:
    """
    Fetches the messages from a session ID and sends them to the LLM model to get an event suggestion.
    This will suggest an event that is most likely to have happened during the session.
    """
    from re import search

    from phospho.lab.language_models import get_provider_and_model, get_sync_client
    from phospho.utils import shorten_text

    session = await get_session_by_id(session_id)
    transcript = await format_session_transcript(session)
    project_id = await get_project_id_from_session(session_id)
    event_descriptions = await get_event_descriptions(project_id)

    provider, model_name = get_provider_and_model(model)
    openai_client = get_sync_client(provider)

    # We look at the full session
    system_prompt = (
        "Here is an exchange between a user and an assistant, your job is to suggest possible events in this exchange and to come up with a name for them, \
        if you don't find anything answer like so: None, otherwise suggest a name and a description for a possible event to detect in this exchange like so: Name: The event name Possible event: Your suggestion here. \
        The event name should be 2-3 words long and the description should be short, 10 to 15 words. \
        \nHere are the existing events:\n- "
        + "\n- ".join(event_descriptions)
    )
    messages = "DISCUSSION START\n" + transcript

    max_tokens_input_lenght = 128 * 1000 - 2000  # We remove 1k for safety
    prompt = shorten_text(messages, max_tokens_input_lenght) + "DISCUSSION END"

    logger.info(f"Event suggestion session: {system_prompt}")
    logger.info(f"Event suggestion prompt: {prompt}")

    try:
        response = openai_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": prompt,
                },
            ],
            max_tokens=50,
        )

        llm_response = response.choices[0].message.content
        logger.info(f"Event suggestion response: {llm_response}")

        regexName = r"Name: (.*)(?=[ \n]Possible event:)"
        regexDescription = r"Possible event: (.*)"

        name = search(regexName, llm_response)
        description = search(regexDescription, llm_response)

        if name is not None and description is not None:
            logger.info(f"Event detected in the session: {name} - {description}")
            return [name.group(1), description.group(1)]

        else:
            logger.info("No event detected in the session.")
            return [
                "No significant event",
                "We couldn't detect any relevant event in this session.",
            ]

    except Exception as e:
        logger.error(f"event_detection call to OpenAI API failed : {e}")

        return ["Error", "An error occured while trying to suggest an event."]


async def add_event_to_session(
    session: Session,
    event: EventDefinition,
    score_range_value: Optional[float] = None,
    score_category_label: Optional[str] = None,
    event_source: str = "owner",
) -> Session:
    """
    Adds an event to a Session
    """
    mongo_db = await get_mongo_db()
    # Check if the event is already in the Session
    if session.events is not None and event.event_name in [
        e.event_name for e in session.events
    ]:
        return session

    if (
        score_range_value is None
        and score_category_label is not None
        and event.score_range_settings.score_type == "category"
        and event.score_range_settings.categories is not None
    ):
        score_range_value = (
            event.score_range_settings.categories.index(score_category_label) + 1
        )
    if score_range_value is None:
        score_range = None
    else:
        score_range = ScoreRange(
            score_type=event.score_range_settings.score_type,
            min=event.score_range_settings.min,
            max=event.score_range_settings.max,
            label=score_category_label,
            value=score_range_value,
        )

    # Add the event to the events collection and to the session
    detected_event_data = Event(
        event_name=event.event_name,
        session_id=session.id,
        project_id=session.project_id,
        source=event_source,
        webhook=event.webhook,
        org_id=session.org_id,
        event_definition=event,
        confirmed=True,
        score_range=score_range,
    )
    _ = await mongo_db["events"].insert_one(detected_event_data.model_dump())

    if session.events is None:
        session.events = []
    session.events.append(detected_event_data)

    # Update the session object
    _ = await mongo_db["sessions"].update_many(
        {"id": session.id, "project_id": session.project_id},
        {"$set": session.model_dump()},
    )

    return session


async def remove_event_from_session(session: Session, event_name: str) -> Session:
    """
    Removes an event from a session
    """
    mongo_db = await get_mongo_db()
    # Check if the event is in the session
    if session.events is not None and event_name in [
        e.event_name for e in session.events
    ]:
        # Mark the event as removed in the events database
        await mongo_db["events"].update_many(
            {"session_id": session.id, "event_name": event_name},
            {
                "$set": {
                    "removed": True,
                    "removal_reason": "removed_by_user_from_session",
                }
            },
        )

        # Remove the event from the session
        session.events = [e for e in session.events if e.event_name != event_name]
        return session
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Event {event_name} not found in session {session.id}",
        )


async def human_eval_session(
    session_model: Session,
    human_eval: str,
) -> Session:
    """
    Update the human eval of a session and the session_flag with "success" or "failure"
    """

    mongo_db = await get_mongo_db()

    flag = cast(Literal["success", "failure"], human_eval)

    await mongo_db["sessions"].update_one(
        {"id": session_model.id},
        {
            "$set": {
                "stats.human_eval": flag,
            }
        },
    )
    session_model.stats.human_eval = flag

    return session_model


async def session_filtering_pipeline_match(
    project_id: str,
    filters: Optional[ProjectDataFilters] = None,
    collection: str = "sessions",
) -> Tuple[Dict[str, object], str]:
    """
    Builds the filtering pipeline for sessions.
    """
    if filters is None:
        filters = ProjectDataFilters()

    match: Dict[str, object] = {"project_id": project_id}

    if filters.sessions_ids is not None:
        match["id"] = {"$in": filters.session_ids}

    if isinstance(filters.created_at_start, datetime.datetime):
        filters.created_at_start = int(filters.created_at_start.timestamp())

    if isinstance(filters.created_at_end, datetime.datetime):
        filters.created_at_end = int(filters.created_at_end.timestamp())

    if filters.created_at_start is not None:
        match["created_at"] = {"$gte": filters.created_at_start}
    if filters.created_at_end is not None:
        match["created_at"] = {
            **match.get("created_at", {}),
            "$lte": filters.created_at_end,
        }

    if filters.metadata is not None:
        for key, value in filters.metadata.items():
            match[f"metadata.{key}"] = value

    if filters.language is not None:
        match["stats.most_common_language"] = filters.language

    if filters.sentiment is not None:
        match["stats.most_common_sentiment_label"] = filters.sentiment

    if filters.flag is not None:
        match["stats.most_common_flag"] = filters.flag

    if filters.event_name is not None:
        collection = "sessions_with_events"
        match["$and"] = [
            {"events": {"$ne": []}},
            {
                "events": {
                    "$elemMatch": {
                        "event_name": {"$in": filters.event_name},
                    }
                }
            },
        ]

    if filters.event_id is not None:
        collection = "sessions_with_events"
        match["$and"] = [
            {"events": {"$ne": []}},
            {
                "events": {
                    "$elemMatch": {
                        "id": {"$in": filters.event_id},
                    }
                }
            },
        ]

    return match, collection
