from app.db.mongo import get_mongo_db
from app.db.models import Task
import pydantic
from fastapi import HTTPException


async def get_task_by_id(task_id: str) -> Task:
    mongo_db = await get_mongo_db()
    task = await mongo_db["tasks"].find_one({"id": task_id})
    if task is None:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")

    # Account for schema discrepancies
    if "id" not in task.keys():
        task["id"] = task_id

    if task["flag"] == "undefined":
        task["flag"] = None

    try:
        task = Task.model_validate(task, strict=True)
    except pydantic.ValidationError as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to validate task {task_id}: {e}"
        )

    return task
