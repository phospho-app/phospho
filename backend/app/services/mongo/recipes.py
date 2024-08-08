import asyncio
from typing import Optional, List
from app.api.platform.models.explore import Pagination
from app.db.mongo import get_mongo_db
from app.services.mongo.events import get_event_definition_from_event_id
from app.services.mongo.extractor import ExtractorClient
from app.services.mongo.projects import get_project_by_id
from app.services.mongo.tasks import get_all_tasks, get_total_nb_of_tasks
from fastapi import HTTPException
from loguru import logger
from phospho.models import EventDefinition, ProjectDataFilters, Recipe


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


async def get_recipe_from_event_id(project_id: str, event_id: str) -> Recipe:
    event_definition = await get_event_definition_from_event_id(
        project_id=project_id, event_id=event_id
    )
    if event_definition.recipe_id is None:
        raise HTTPException(
            status_code=404,
            detail=f"Event {event_definition.event_name} has no recipe_id for project {project_id}.",
        )

    recipe = await get_recipe_by_id(recipe_id=event_definition.recipe_id)
    return recipe


async def get_recipe_from_event_definition_id(
    project_id: str, event_definition_id: str
) -> Recipe:
    mongo_db = await get_mongo_db()
    event_definition = await mongo_db["event_definitions"].find_one(
        {"id": event_definition_id}
    )
    event_definition_validated = EventDefinition.model_validate(event_definition)
    if event_definition_validated.recipe_id is None:
        raise HTTPException(
            status_code=404,
            detail=f"Event {event_definition.event_name} has no recipe_id for project {project_id}.",
        )

    recipe = await get_recipe_by_id(recipe_id=event_definition_validated.recipe_id)
    return recipe


async def run_recipe_on_tasks_batched(
    project_id: str,
    recipe: Recipe,
    org_id: str,
    sample_rate: Optional[float] = None,
    filters: Optional[ProjectDataFilters] = None,
) -> None:
    """
    Run a recipe_id on all tasks of a project.

    Batched to avoid memory issues.
    """
    if filters is None:
        filters = ProjectDataFilters()

    total_nb_tasks = await get_total_nb_of_tasks(
        project_id=project_id,
        filters=filters,
    )
    if not total_nb_tasks:
        logger.warning(
            f"No tasks found for project {project_id} with filters {filters}. Skipping."
        )
        return

    if sample_rate is not None:
        # Clamp sample rate between 0 and 1
        sample_rate = max(0, min(1, sample_rate))
        sample_size = int(total_nb_tasks * sample_rate)
    else:
        sample_size = total_nb_tasks

    # Batch the tasks to avoid memory issues
    batch_size = 128
    nb_batches = sample_size // batch_size
    extractor_client = ExtractorClient(
        project_id=project_id,
        org_id=org_id,
    )
    for i in range(nb_batches + 1):
        tasks = await get_all_tasks(
            project_id=project_id,
            filters=filters,
            pagination=Pagination(page=i, per_page=batch_size),
        )
        await extractor_client.run_recipe_on_tasks(
            tasks=tasks,
            recipe=recipe,
        )
        # Add a sleep to avoid overloading the extractor
        await asyncio.sleep(5)


async def run_recipe_types_on_tasks(
    project_id: str,
    recipe_types: List[str],
    org_id: str,
    filters: Optional[ProjectDataFilters],
) -> None:
    """
    Run multiple recipes of different types on tasks of a project
    """
    if filters is None:
        filters = ProjectDataFilters()

    logger.debug(f"Running recipes of types {recipe_types} on project {project_id}")

    for recipe_type in recipe_types:
        if recipe_type == "event_detection":
            # TODO: Fetch recipes from events

            # Fetch the project
            project = await get_project_by_id(project_id)
            recipes = []
            for event_name, event_definition in project.settings.events.items():
                try:
                    recipe = await get_recipe_by_id(event_definition.recipe_id)
                    recipes.append(recipe)
                except HTTPException as e:
                    logger.warning(
                        f"Recipe for event {event_name} not found. Skipping.\nFull Error: {e}"
                    )

            for recipe in recipes:
                await run_recipe_on_tasks_batched(
                    project_id=project_id,
                    recipe=recipe,
                    org_id=org_id,
                    sample_rate=None,
                    filters=filters,
                )
        elif recipe_type == "evaluation" or recipe_type == "sentiment_language":
            recipe = Recipe(
                recipe_type=recipe_type,
                org_id=org_id,
                project_id=project_id,
            )
            await run_recipe_on_tasks_batched(
                project_id=project_id,
                recipe=recipe,
                org_id=org_id,
                sample_rate=None,
                filters=filters,
            )
        elif recipe_type == "clustering":
            # TODO: Implement clustering
            logger.warning("Clustering not implemented yet. Skipping.")
        else:
            logger.warning(f"Recipe type {recipe_type} not found. Skipping.")
