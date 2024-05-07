from app.db.models import EventDefinition, Recipe
from app.db.mongo import get_mongo_db
from fastapi import HTTPException
from loguru import logger
from app.services.mongo.extractor import run_recipe_on_tasks
from app.services.mongo.projects import get_all_tasks
from app.api.platform.models import EventBackfillRequest


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


async def get_recipe_by_id(recipe_id: str) -> Recipe:
    """
    Get a recipe by its id
    """
    mongo_db = await get_mongo_db()
    recipe = await mongo_db["recipes"].find_one({"id": recipe_id})
    if not recipe:
        raise HTTPException(status_code=404, detail="Recipe not found")
    validated_recipe = Recipe.model_validate(recipe)
    return validated_recipe


async def run_event_detection_on_timeframe(
    project_id: str, event_backfill_request: EventBackfillRequest
) -> None:
    """
    Run event detection on a given event_id and event_data
    """
    event_definition = await get_event_definition_from_event_id(
        project_id, event_backfill_request.event_id
    )
    if event_definition.recipe_id is None:
        logger.error(
            f"Event {event_definition.event_name} has no recipe_id for project {project_id}. Canceling."
        )
        return
    recipe = await get_recipe_by_id(recipe_id=event_definition.recipe_id)
    tasks = await get_all_tasks(
        project_id=project_id,
        created_at_start=event_backfill_request.created_at_start,
        created_at_end=event_backfill_request.created_at_end,
        sample_rate=event_backfill_request.sample_rate,
    )
    await run_recipe_on_tasks(tasks=tasks, recipe=recipe)
    return None
