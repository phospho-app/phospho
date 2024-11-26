from typing import Literal

from pydantic import BaseModel
from pydantic.fields import Field

from phospho_backend.db.models import FlattenedTask, Task
from phospho_backend.utils import generate_uuid


class Tasks(BaseModel):
    tasks: list[Task]


class TaskCreationRequest(BaseModel):
    task_id: str | None = Field(default_factory=generate_uuid)
    session_id: str | None = None
    input: str
    additional_input: dict | None = None
    output: str
    additional_output: dict | None = None
    data: dict | None = None
    metadata: dict | None = None
    project_id: str
    flag: Literal["success", "failure"] | None = None


class TaskFlagRequest(BaseModel):
    flag: Literal["success", "failure"] | None = None
    source: str | None = "owner"
    notes: str | None = None
    project_id: str | None = None


class TaskHumanEvalRequest(BaseModel):
    human_eval: Literal["success", "failure"] | None = None
    project_id: str | None = None
    source: str | None = "owner"
    notes: str | None = None


class TaskUpdateRequest(BaseModel):
    metadata: dict | None = None
    data: dict | None = None
    notes: str | None = None
    flag: Literal["success", "failure"] | None = None
    flag_source: str | None = None


class FlattenedTasks(BaseModel):
    flattened_tasks: list[FlattenedTask]
