from pydantic import BaseModel
from typing import List, Optional, Literal

from app.db.models import Task, Event, Recipe
from phospho.lab import Message
from phospho.models import SentimentObject

from app.utils import generate_timestamp, generate_uuid
from pydantic import Field


class RunMainPipelineOnTaskRequest(BaseModel):
    task: Task
    save_results: bool = False


class RunMainPipelineOnMessagesRequest(BaseModel):
    project_id: str
    messages: List[Message]


class PipelineResults(BaseModel):
    events: List[Event]
    flag: Optional[Literal["success", "failure"]]
    language: Optional[str] = None
    sentiment: Optional[SentimentObject] = None


class RunRecipeOnTaskRequest(BaseModel):
    tasks: List[Task]
    recipe: Recipe


class AugmentedOpenTelemetryData(BaseModel):
    project_id: str
    org_id: str
    open_telemetry_data: dict


class EvaluationModel(BaseModel):
    id: int = Field(default_factory=generate_uuid)
    project_id: str
    system_prompt: str
    created_at: int = Field(default_factory=generate_timestamp)
    removed: bool = False
