from typing import List, Optional
from app.db.models import Session, Project, Task
from app.db.mongo import get_mongo_db

from loguru import logger
from fastapi import HTTPException

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
        await mongo_db["sessions"]
        .aggregate(
            [
                {"$match": {"id": session_id}},
                {
                    "$lookup": {
                        "from": "events",
                        "localField": "id",
                        "foreignField": "session_id",
                        "as": "events",
                    }
                },
                {
                    "$project": {
                        "id": 1,
                        "created_at": 1,
                        "project_id": 1,
                        "org_id": 1,
                        "data": 1,
                        "notes": 1,
                        "preview": 1,
                        "environment": 1,
                        "events": 1,
                        "tasks": 1,
                        "session_length": 1,
                    }
                },
            ]
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
        await mongo_db["tasks"]
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
    update_result = await mongo_db["sessions"].update_one(
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
    model: str = "openai:gpt-4-turbo",
) -> list[str]:
    """
    Fetches the messages from a session ID and sends them to the LLM model to get an event suggestion.
    This will suggest an event that is most likely to have happened during the session.
    """
    from phospho.utils import shorten_text
    from phospho.lab.language_models import get_provider_and_model, get_sync_client
    from re import search

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
