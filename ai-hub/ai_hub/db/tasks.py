from typing import List, Optional

from loguru import logger
from phospho.models import ProjectDataFilters, Task
from phospho_backend.services.mongo.query_builder import QueryBuilder

from ai_hub.core import config
from ai_hub.db.mongo import get_mongo_db
from ai_hub.models.clusterings import Clustering


async def load_tasks(
    project_id: str,
    clustering: Clustering,
    filters: Optional[ProjectDataFilters] = None,
    limit: Optional[int] = 4000,
) -> Optional[List[Task]]:
    mongo_db = await get_mongo_db()
    # Get the most recent tasks of the project
    query_builder = QueryBuilder(
        project_id=project_id,
        fetch_objects="tasks",
        filters=filters,
    )

    pipeline = await query_builder.build()

    data = await mongo_db["tasks"].aggregate(pipeline).to_list(length=limit)

    if data is None:
        logger.warning(f"No tasks found for project {project_id}")
        # Delete the clustering object in the database
        await mongo_db[config.CLUSTERINGS_COLLECTION].delete_one({"id": clustering.id})
        return None

    # Make the tasks a list of Task objects
    data = [Task.model_validate(task) for task in data]
    if len(data) == 0:
        logger.warning(f"No valid tasks found in project {project_id}")
        # Delete the clustering object in the database
        await mongo_db[config.CLUSTERINGS_COLLECTION].delete_one({"id": clustering.id})
        return None

    logger.debug(f"Nb Tasks: {len(data)}")

    if len(data) < config.MIN_NUMBER_OF_EMBEDDINGS_FOR_CLUSTERING:
        logger.warning(f"No enough tasks for clustering {project_id}")
        # Delete the clustering object in the database
        await mongo_db[config.CLUSTERINGS_COLLECTION].delete_one({"id": clustering.id})
        return None
    return data
