from pydantic import BaseModel
from typing import List, Optional, Literal

from app.db.models import Task, Event
from phospho.lab import Message


class RunMainPipelineOnTaskRequest(BaseModel):
    task: Task


class RunMainPipelineOnMessagesRequest(BaseModel):
    messages: List[Message]


class PipelineResults(BaseModel):
    events: List[Event]
    flag: Optional[Literal["success", "failure"]]
