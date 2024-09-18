from app.db.mongo import get_mongo_db
from loguru import logger


async def rename_clustering(project_id: str, clustering_id: str, new_name: str):
    """
    Rename a clustering.
    """
    mongo_db = await get_mongo_db()

    result = await mongo_db["private-clusterings"].update_one(
        {"id": clustering_id, "project_id": project_id},
        {"$set": {"name": new_name}},
    )

    logger.debug(f"Renamed clustering {clustering_id} to {new_name}")
    logger.debug(f"{result}")
