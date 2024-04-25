from app.db.models import EventDefinition
from app.db.mongo import get_mongo_db
from fastapi import HTTPException
from loguru import logger


async def get_event_definition_from_event_id(
    project_id: str, event_id: str
) -> EventDefinition:
    """
    Utility function to get an EventDefinition in project settings from a given event_id
    """
    mongo_db = await get_mongo_db()
    event_definition = (
        await mongo_db["projects"]
        .aggregate(
            [
                {"$match": {"id": project_id}},
                {"$project": {"events": {"$objectToArray": "$$ROOT.settings.events"}}},
                {"$unwind": "$events"},
                # Use $filter to get the event definition from the array of events
                {"$match": {"events.v.id": event_id}},
                {"$project": {"events": "$events.v"}},
                {"$replaceRoot": {"newRoot": "$events"}},
            ]
        )
        .to_list(1)
    )
    if not event_definition:
        raise HTTPException(status_code=404, detail="Event definition not found")
    try:
        validated_event = EventDefinition.model_validate(event_definition[0])
        return validated_event
    except Exception as e:
        logger.error(f"Error validating event: {e}")
        raise HTTPException(status_code=500, detail="Error validating event")


async def get_event_from_name_and_project_id(
    project_id: str, event_name: str
) -> EventDefinition:
    """
    Utility function to get an event from a given project_id and event_name
    """
    mongo_db = await get_mongo_db()
    event_definition = (
        await mongo_db["projects"]
        .aggregate(
            [
                {"$match": {"id": project_id}},
                {"$project": {"events": {"$objectToArray": "$$ROOT.settings.events"}}},
                {"$unwind": "$events"},
                # Use $filter to get the event definition from the array of events
                {"$match": {"events.v.name": event_name}},
                {"$project": {"events": "$events.v"}},
                {"$replaceRoot": {"newRoot": "$events"}},
            ]
        )
        .to_list(1)
    )
    if not event_definition:
        raise HTTPException(status_code=404, detail="Event definition not found")
    validated_event = EventDefinition.model_validate(event_definition[0])
    return validated_event
