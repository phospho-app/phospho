from pydantic import BaseModel
from typing import List, Optional, Literal

from app.db.models import Task
from pydantic.fields import Field

from app.utils import generate_uuid


class Tasks(BaseModel):
    tasks: List[Task]


class TaskCreationRequest(BaseModel):
    task_id: Optional[str] = Field(default_factory=generate_uuid)
    session_id: Optional[str] = None
    input: str
    additional_input: Optional[dict] = None
    output: str
    additional_output: Optional[dict] = None
    data: Optional[dict] = None
    metadata: Optional[dict] = None
    project_id: str
    flag: Optional[Literal["success", "failure"]] = None


class TaskFlagRequest(BaseModel):
    flag: Optional[Literal["success", "failure"]] = None
    source: Optional[str] = "owner"
    notes: Optional[str] = None
    project_id: Optional[str] = None


class TaskUpdateRequest(BaseModel):
    metadata: Optional[dict] = None
    data: Optional[dict] = None
    notes: Optional[str] = None
    flag: Optional[Literal["success", "failure"]] = None
    flag_source: Optional[str] = None


class FlattenedTask(BaseModel, extra="allow"):
    task_id: str
    task_input: Optional[str] = None
    task_output: Optional[str] = None
    task_metadata: Optional[dict] = None
    task_eval: Optional[Literal["success", "failure"]] = None
    task_eval_source: Optional[str] = None
    task_eval_at: Optional[int] = None
    task_created_at: Optional[int] = None
    session_id: Optional[str] = None
    session_length: Optional[int] = None
    event_name: Optional[str] = None
    event_created_at: Optional[int] = None


class FlattenedTasks(BaseModel):
    flattened_tasks: List[FlattenedTask]
