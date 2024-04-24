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

    # If event_name not in project_data.settings.events.values(), add it based on the key
    push_to_db = False
    if (
        "settings" in project_data.keys()
        and "events" in project_data["settings"].keys()
    ):
        for event_name, event in project_data["settings"]["events"].items():
            if "event_name" not in event.keys():
                project_data["settings"]["events"][event_name][
                    "event_name"
                ] = event_name
                push_to_db = True
            if "org_id" not in event.keys():
                project_data["settings"]["events"][event_name]["org_id"] = project_data[
                    "org_id"
                ]
                push_to_db = True
            if "project_id" not in event.keys():
                project_data["settings"]["events"][event_name][
                    "project_id"
                ] = project_data["id"]
                push_to_db = True

    try:
        project = Project(**project_data)
        # push the updated project to the database
        if push_to_db:
            mongo_db["projects"].update_one(
                {"_id": project_data["_id"]}, {"$set": project.model_dump()}
            )
    except Exception as e:
        logger.warning(f"Error validating model of project {project_data.id}: {e}")
        raise ValueError(f"Error validating project model: {e}")

    return project
