from app.db.models import Task
from pydantic import BaseModel
from typing import List


class TaskForBackfill(Task):
    # We override the created_at field to make it required
    created_at: int


class BackfillBatchRequest(BaseModel):
    tasks: List[TaskForBackfill]
