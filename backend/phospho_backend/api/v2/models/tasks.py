from pydantic import BaseModel
from typing import List, Optional, Literal

from phospho_backend.db.models import Task, FlattenedTask
from pydantic.fields import Field

from phospho_backend.utils import generate_uuid


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


class TaskHumanEvalRequest(BaseModel):
    human_eval: Optional[Literal["success", "failure"]] = None
    project_id: Optional[str] = None
    source: Optional[str] = "owner"
    notes: Optional[str] = None


class TaskUpdateRequest(BaseModel):
    metadata: Optional[dict] = None
    data: Optional[dict] = None
    notes: Optional[str] = None
    flag: Optional[Literal["success", "failure"]] = None
    flag_source: Optional[str] = None


class FlattenedTasks(BaseModel):
    flattened_tasks: List[FlattenedTask]
