from typing import Dict, Optional

from langdetect import detect  # type: ignore
from loguru import logger

from extractor.db.models import Task
from extractor.db.mongo import get_mongo_db


async def get_task_by_id(task_id: str) -> Task:
    mongo_db = await get_mongo_db()
    task = await mongo_db["tasks"].find_one({"id": task_id})
    if task is None:
        logger.error(f"Task with id {task_id} not found")
        raise ValueError(f"Task with id {task_id} not found")

    # Account for schema discrepancies
    if "id" not in task.keys():
        task["id"] = task_id

    if task["flag"] == "undefined":
        task["flag"] = None

    task = Task.model_validate(task, strict=True)

    return task


async def detect_language_pipeline(task: Task) -> str:
    """
    (OBSOLETE)

    Archived, we use Google Sentiment Analysis API to detect language.
    Doesn't work well with short texts, but strong on longer formats.

    Uses the langdetect library to detect the language of a given text
    returns a two letter identifier for the language, e.g. 'en' for English, 'fr' for French, etc.
    """
    mongo_db = await get_mongo_db()
    try:
        language = detect(task.input)
        mongo_db["tasks"].update_one(
            {
                "id": task.id,
                "project_id": task.project_id,
            },
            {"$set": {"language": language}},
        )
        return language
    except Exception as e:
        logger.info(f"Failed to detect language: {e}")
        return "unknown"


async def compute_task_position(
    project_id: str, session_ids: Optional[list[str]] = None
):
    """
    Executes an aggregation pipeline to compute the task position for each task.
    """
    mongo_db = await get_mongo_db()

    main_filter: Dict[str, object] = {"project_id": project_id}
    if session_ids is not None:
        main_filter["id"] = {"$in": session_ids}

    pipeline = [
        {
            "$match": main_filter,
        },
        {
            "$lookup": {
                "from": "tasks",
                "localField": "id",
                "foreignField": "session_id",
                "as": "tasks",
            }
        },
        {
            "$set": {
                "tasks": {
                    "$sortArray": {
                        "input": "$tasks",
                        "sortBy": {"tasks.created_at": 1},
                    },
                }
            }
        },
        # Transform to get 1 doc = 1 task. We also add the task position.
        {"$unwind": {"path": "$tasks", "includeArrayIndex": "task_position"}},
        # Set "is_last_task" to True for the task where task_position is == session.session_length - 1
        {
            "$set": {
                "tasks.is_last_task": {
                    "$eq": ["$task_position", {"$subtract": ["$session_length", 1]}]
                }
            }
        },
        {
            "$project": {
                "id": "$tasks.id",
                "task_position": {"$add": ["$task_position", 1]},
                "is_last_task": "$tasks.is_last_task",
                "_id": 0,
            }
        },
        {
            "$merge": {
                "into": "tasks",
                "on": "id",
                "whenMatched": "merge",
                "whenNotMatched": "discard",
            }
        },
    ]

    await mongo_db["sessions"].aggregate(pipeline).to_list(length=None)
