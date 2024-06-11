from app.api.platform.models.explore import Pagination
from app.db.mongo import get_mongo_db
from app.services.mongo.extractor import run_recipe_on_tasks
from app.services.mongo.tasks import get_all_tasks, get_total_nb_of_tasks
from fastapi import HTTPException
from phospho.models import ProjectDataFilters, Recipe


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


async def run_recipe_on_tasks_batched(
    project_id: str,
    recipe_id: str,
    org_id: str,
    sample_rate: float,
    filters: ProjectDataFilters,
):
    """
    Run a recipe_id on all tasks of a project.

    Batched to avoid memory issues.
    """
    if recipe_id == "evaluation":
        recipe = Recipe(
            org_id=org_id,
            project_id=project_id,
            status="active",
            recipe_type="evaluation",
        )
    else:
        recipe = await get_recipe_by_id(recipe_id=recipe_id)

    total_nb_tasks = await get_total_nb_of_tasks(
        project_id=project_id,
        filters=filters,
    )
    if sample_rate is not None:
        # Clamp sample rate between 0 and 1
        sample_rate = max(0, min(1, sample_rate))
        sample_size = int(total_nb_tasks * sample_rate)
    else:
        sample_size = total_nb_tasks

    # Batch the tasks to avoid memory issues
    batch_size = 256
    nb_batches = sample_size // batch_size
    for i in range(nb_batches + 1):
        tasks = await get_all_tasks(
            project_id=project_id,
            filters=filters,
            pagination=Pagination(page=i, per_page=batch_size),
        )
        await run_recipe_on_tasks(tasks=tasks, recipe=recipe, org_id=org_id)
