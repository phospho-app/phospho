from typing import Dict, List, Optional

from loguru import logger
from phospho.models import ProjectDataFilters
from phospho_backend.services.mongo.query_builder import QueryBuilder

from ai_hub.db.mongo import get_mongo_db
from ai_hub.models.clusterings import Clustering
from ai_hub.models.users import User


async def load_users(
    project_id: str,
    clustering: Clustering,
    filters: Optional[ProjectDataFilters] = None,
    limit: Optional[int] = 4000,
) -> List[User]:
    """
    Load users from the database
    """

    mongo_db = await get_mongo_db()

    query_builder = QueryBuilder(
        project_id=project_id,
        fetch_objects="tasks",
        filters=filters,
    )

    pipeline = await query_builder.build()

    pipeline.extend(
        [
            {"$match": {"metadata.user_id": {"$exists": True, "$ne": None}}},
            {
                "$group": {
                    "_id": "$metadata.user_id",
                }
            },
        ]
    )

    if limit is not None:
        pipeline.append(
            {"$limit": limit},
        )

    data = await mongo_db["tasks"].aggregate(pipeline).to_list(length=limit)

    if len(data) == 0:
        return []

    user_ids: List[str] = [user["_id"] for user in data]

    users: Dict[str, User] = {}
    for user_id in user_ids:
        users[user_id] = User(
            org_id=clustering.org_id, project_id=project_id, id=user_id
        )

    pipeline = [
        {
            "$match": {
                "project_id": project_id,
                "metadata.user_id": {"$in": user_ids},
            }
        },
        {
            "$group": {
                "_id": "$session_id",
                "user_id": {"$first": "$metadata.user_id"},
            }
        },
    ]

    data = await mongo_db["tasks"].aggregate(pipeline).to_list(length=None)
    logger.debug(f"data: {data}")

    for session in data:
        user_id = session["user_id"]
        if user_id not in users.keys():
            logger.warning(f"User {user_id} not found in users")
            continue
        users[user_id].sessions_ids.append(session["_id"])

    logger.debug(f"users: {users}")

    return list(users.values())
