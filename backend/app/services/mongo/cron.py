from app.db.mongo import get_mongo_db


async def fetch_projects_to_sync(type: str = "langsmith"):
    """
    Fetch the project ids to sync
    """
    mongo_db = await get_mongo_db()
    project_ids = await mongo_db["keys"].distinct("project_id", {"type": type})
    return project_ids
