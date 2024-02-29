from loguru import logger
from app.db.mongo import get_mongo_db
from app.db.models import Project


async def get_project_by_id(project_id: str) -> Project:
    mongo_db = await get_mongo_db()

    # doc = db.get_document("projects", project_id).get()
    project_data = await mongo_db["projects"].find_one({"id": project_id})

    if project_data is None:
        raise ValueError(f"Project {project_id} not found")

    # Handle different names of the same field
    if "creation_date" in project_data.keys():
        project_data["created_at"] = project_data["creation_date"]

    if "id" not in project_data.keys():
        project_data["id"] = project_data["_id"]

    if "org_id" not in project_data.keys():
        raise ValueError(f"Project {project_id} not found")

    try:
        project = Project(**project_data)
    except Exception as e:
        logger.warning(f"Error validating model of project {project_data.id}: {e}")
        raise ValueError(f"Error validating project model: {e}")

    return project
