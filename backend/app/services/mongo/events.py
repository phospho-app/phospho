from app.db.models import (
    Event,
)
from app.db.mongo import get_mongo_db
from loguru import logger


async def get_event_from_event_id(event_id: str) -> Event:
    """
    Utility function to get an event from a given event_id
    """
    mongo_db = await get_mongo_db()
    event = await mongo_db["events"].find_one({"id": event_id})
    try:
        validated_event = Event.model_validate(event)
        return validated_event
    except Exception as e:
        logger.error(f"Error validating event: {e}")


async def get_event_from_name_and_project_id(project_id: str, event_name: str) -> Event:
    """
    Utility function to get an event from a given project_id and event_name
    """
    mongo_db = await get_mongo_db()
    event = await mongo_db["events"].find_one(
        {"project_id": project_id, "name": event_name}
    )
    validated_event = Event.model_validate(event)
    return validated_event
