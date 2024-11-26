from typing import List, Optional
from phospho.models import Session, ProjectDataFilters

from ai_hub.models.clusterings import Clustering
from ai_hub.db.mongo import get_mongo_db
from ai_hub.core import config
from loguru import logger

from phospho_backend.services.mongo.query_builder import QueryBuilder


async def load_sessions(
    project_id: str,
    clustering: Optional[Clustering] = None,
    filters: Optional[ProjectDataFilters] = None,
    limit: Optional[int] = 4000,
) -> Optional[List[Session]]:
    mongo_db = await get_mongo_db()

    query_builder = QueryBuilder(
        project_id=project_id,
        fetch_objects="sessions",
        filters=filters,
    )

    pipeline = await query_builder.build()

    data = await mongo_db["sessions"].aggregate(pipeline).to_list(length=limit)

    if clustering is not None:
        if data is None:
            logger.warning(f"No tasks found for project {project_id}")
            # Delete the clustering object in the database
            await mongo_db[config.CLUSTERINGS_COLLECTION].delete_one(
                {"id": clustering.id}
            )
            return None

        # Make the sessions a list of Session objects
        data = [Session.model_validate(session) for session in data]
        if len(data) == 0:
            logger.warning(f"No valid tasks found in project {project_id}")
            # Delete the clustering object in the database
            await mongo_db[config.CLUSTERINGS_COLLECTION].delete_one(
                {"id": clustering.id}
            )
            return None

        logger.debug(f"Nb Sessions: {len(data)}")

        if len(data) < config.MIN_NUMBER_OF_EMBEDDINGS_FOR_CLUSTERING:
            logger.warning(f"No enough sessions for clustering {project_id}")
            # Delete the clustering object in the database
            await mongo_db[config.CLUSTERINGS_COLLECTION].delete_one(
                {"id": clustering.id}
            )
            return None
    return data
