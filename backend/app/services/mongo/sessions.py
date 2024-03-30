from typing import List, Optional
from app.db.models import Session, Task
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


async def format_session_transcript(session: Session) -> str:
    """
    Format the transcript of a session into a human-readable string.

    Eg:
    User: Hello
    Assistant: Hi there!
    """
    transcript = ""
    mongo_db = await get_mongo_db()

    def append_to_transcript(task_data, error):
        if task_data:
            transcript += f"User: {task_data['input']}\n "
            transcript += f"Assistant: {task_data.get('output', '')}\n "

    await (
        mongo_db["tasks"]
        .find({"session_id": session.id})
        .sort("created_at", 1)
        .each(append_to_transcript)
    )

    return transcript


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
