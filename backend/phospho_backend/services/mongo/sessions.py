from typing import Literal, cast

from phospho_backend.api.platform.models.explore import Pagination, Sorting
from phospho_backend.db.models import Event, EventDefinition, Session, Task
from phospho_backend.db.mongo import get_mongo_db
from phospho_backend.services.mongo.query_builder import QueryBuilder
from fastapi import HTTPException
from loguru import logger

from phospho.models import ProjectDataFilters, ScoreRange
from phospho.utils import is_jsonable
from phospho.lab.language_models import get_provider_and_model, get_sync_client


async def create_session(
    project_id: str, org_id: str, data: dict | None = None
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
    query_builder = QueryBuilder(
        project_id=None,
        fetch_objects="sessions_with_events",
        filters=ProjectDataFilters(sessions_ids=[session_id]),
    )
    pipeline = await query_builder.build()
    found_session = await mongo_db["sessions"].aggregate(pipeline).to_list(length=1)
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


async def fetch_session_tasks(
    project_id: str, session_id: str, limit: int = 1000
) -> list[Task]:
    """
    Fetch all tasks for a given session id.
    """
    mongo_db = await get_mongo_db()
    query_builder = QueryBuilder(
        project_id=project_id,
        fetch_objects="tasks_with_events",
        filters=ProjectDataFilters(sessions_ids=[session_id]),
    )
    pipeline = await query_builder.build()
    tasks = (
        await mongo_db["tasks"]
        .aggregate(
            pipeline
            + [
                {"$sort": {"created_at": -1}},
            ]
        )
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

    tasks = await fetch_session_tasks(
        project_id=session.project_id, session_id=session.id
    )

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
    project_id: str, filters: ProjectDataFilters | None = None
):
    """
    Executes an aggregation pipeline to compute the task position for each task.
    """
    mongo_db = await get_mongo_db()

    query_filter = QueryBuilder(
        project_id=project_id, filters=filters, fetch_objects="sessions_with_tasks"
    )
    pipeline = await query_filter.build()

    pipeline += [
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


async def event_suggestion(
    session_id: str,
    model: str = "openai:gpt-4o",
) -> list[str]:
    """
    Fetches the messages from a session ID and sends them to the LLM model to get an event suggestion.
    This will suggest an event that is most likely to have happened during the session.
    """
    from re import search

    from phospho_backend.services.mongo.projects import get_project_by_id

    session = await get_session_by_id(session_id)
    project = await get_project_by_id(session.project_id)

    formatted_tags_list = [
        f"Tag name: {event_definition.event_name}\nDescription: {event_definition.description}"
        for event_name, event_definition in project.settings.events.items()
        if event_definition.score_range_settings.score_type == "confidence"
    ]

    transcript = await format_session_transcript(session)

    provider, model_name = get_provider_and_model(model)
    openai_client = get_sync_client(provider)

    # We look at the full session
    existing_tags = "\n- ".join(formatted_tags_list)
    system_prompt = f"""You are a professional annotator that suggests tags to label conversations. 
Your reply follows the following format:
---
Name: The tag name, 1-3 words.
Description: A short description of the tag, in 10-15 words, that explains what it represents.
---

For reference, here are the existing tags in this project:
<existing_tags>
- {existing_tags}
</existing_tags>
"""
    prompt = f"""Please suggest a new tag, if relevant, for the following conversation:
<transcript>
{transcript}
</transcript>"""

    logger.info(f"Tag suggestion system prompt: {system_prompt}")
    logger.info(f"Tag suggestion prompt: {prompt}")

    try:
        response = openai_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt},
            ],
            max_tokens=120,
        )

        llm_response = response.choices[0].message.content
        if llm_response is None:
            return ["Error", "No response from the model."]

        logger.info(f"Tag suggestion response: {llm_response}")

        regexName = r"Name: (.*)(?=[ \n]Description:)"
        regexDescription = r"Description: (.*)"

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
        return ["Error", str(e)]


async def add_event_to_session(
    session: Session,
    event: EventDefinition,
    score_range_value: float | None = None,
    score_category_label: str | None = None,
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


async def get_all_sessions(
    project_id: str,
    limit: int = 1000,
    filters: ProjectDataFilters | None = None,
    get_events: bool = True,
    get_tasks: bool = False,
    pagination: Pagination | None = None,
    sorting: list[Sorting] | None = None,
) -> list[Session]:
    """
    Fetch all the sessions of a project.
    """
    mongo_db = await get_mongo_db()

    fetch_objects: Literal["sessions", "sessions_with_events"] = "sessions"
    if get_events and not pagination:
        fetch_objects = "sessions_with_events"

    query_builder = QueryBuilder(
        project_id=project_id,
        filters=filters,
        fetch_objects=fetch_objects,
    )
    pipeline = await query_builder.build()

    # To avoid the sort to OOM on Serverless MongoDB executor, we restrain the pipeline to the necessary fields...
    if sorting is None:
        sorting_dict = {"last_message_ts": -1}
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
