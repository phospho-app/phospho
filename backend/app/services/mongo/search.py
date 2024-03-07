from typing import List, Tuple

import openai
from app.db.models import Session, Task
from app.db.mongo import get_mongo_db
from app.db.qdrant import get_qdrant, models
from loguru import logger

openai_client = openai.AsyncClient()


async def search_tasks_in_project(
    project_id: str,
    search_query: str,
) -> List[Task]:
    mongo_db = await get_mongo_db()
    qdrant_db = await get_qdrant()
    # Embed the query
    try:
        query_embedding = await openai_client.embeddings.create(
            input=search_query, model="text-embedding-3-small"
        )
    except openai.APIError as e:
        # If the query is too short, we can't embed it
        # In this case, we just return an empty list
        logger.warning(f"Error while embedding the query: {e}")
        return []

    # Search in the project
    found_vectors = await qdrant_db.search(
        collection_name="tasks",
        query_vector=query_embedding.data[0].embedding,
        query_filter=models.Filter(
            must=[
                models.FieldCondition(
                    key="project_id", match=models.MatchValue(value=project_id)
                )
            ]
        ),
        limit=5,
        # score_threshold=0.5,
    )
    foud_vectors_mapping = {
        vector.payload.get("task_id"): vector
        for vector in found_vectors
        if vector.payload is not None
        and vector.payload.get("task_id", None) is not None
    }

    # Get the tasks
    tasks = (
        await mongo_db["tasks"]
        .find({"id": {"$in": list(foud_vectors_mapping.keys())}})
        .to_list(length=None)
    )

    # Sort the tasks by the order of the found_vectors
    tasks = sorted(
        tasks,
        key=lambda task: foud_vectors_mapping[task["id"]].score,
        reverse=True,
    )

    # Return the tasks
    tasks = [Task.model_validate(task) for task in tasks]
    return tasks


async def search_sessions_in_project(
    project_id: str,
    search_query: str,
) -> Tuple[
    List[Task],
    List[Session],
]:
    relevant_tasks = await search_tasks_in_project(
        project_id=project_id,
        search_query=search_query,
    )
    # Find the sessions that contain the relevant tasks
    mongo_db = await get_mongo_db()
    relevant_sessions = (
        await mongo_db["sessions"]
        .find(
            {
                "project_id": project_id,
                "id": {"$in": [task.session_id for task in relevant_tasks]},
            }
        )
        .to_list(length=None)
    )
    relevant_sessions = [
        Session.model_validate(session) for session in relevant_sessions
    ]
    return relevant_tasks, relevant_sessions
