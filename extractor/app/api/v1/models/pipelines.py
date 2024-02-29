from pydantic import BaseModel
from typing import List

from app.db.models import Task


class MainPipelineRequest(BaseModel):
    task: Task
