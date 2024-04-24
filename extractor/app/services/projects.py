from loguru import logger
from app.db.mongo import get_mongo_db
from app.db.models import Project, Recipe


async def get_project_by_id(project_id: str) -> Project:
    mongo_db = await get_mongo_db()

    # doc = db.get_document("projects", project_id).get()
    project_data = await mongo_db["projects"].find_one({"id": project_id})

    if project_data is None:
        raise ValueError(f"Project {project_id} not found")

    try:
        project = Project.from_previous(project_data)
        for event_name, event in project.settings.events.items():
            if not event.recipe_id:
                recipe = Recipe(
                    org_id=project.org_id,
                    project_id=project.id,
                    recipe_type="event_detection",
                    parameters=event.model_dump(),
                )
                mongo_db["recipes"].insert_one(recipe.model_dump())
                project.settings.events[event_name].recipe_id = recipe.id
        # If the project dict is different from project_data, update the project_data
        if project.model_dump() != project_data:
            mongo_db["projects"].update_one(
                {"_id": project_data["_id"]}, {"$set": project.model_dump()}
            )
    except Exception as e:
        logger.warning(f"Error validating model of project {project_data.id}: {e}")
        raise ValueError(f"Error validating project model: {e}")

    return project
