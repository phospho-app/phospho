from pydantic import BaseModel
from typing import List, Optional, Literal

from app.db.models import Task, Event, Job
from phospho.lab import Message


class RunMainPipelineOnTaskRequest(BaseModel):
    task: Task


class RunMainPipelineOnMessagesRequest(BaseModel):
    project_id: str
    messages: List[Message]


class PipelineResults(BaseModel):
    events: List[Event]
    flag: Optional[Literal["success", "failure"]]


class RunJobOnTasksRequest(BaseModel):
    tasks: List[Task]
    job: Job
