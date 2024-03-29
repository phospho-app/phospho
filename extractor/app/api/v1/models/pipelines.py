from pydantic import BaseModel
from typing import List, Optional, Literal

from app.db.models import Task, Event


class MainPipelineRequest(BaseModel):
    task: Task


class PipelineResults(BaseModel):
    events: List[Event]
    flag: Optional[Literal["success", "failure"]]
