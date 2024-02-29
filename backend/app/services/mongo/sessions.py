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
    session = await mongo_db["sessions"].find_one({"id": session_id})
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
