from pydantic import BaseModel
from typing import List, Optional, Literal

from app.db.models import Task, Event, Recipe
from phospho.lab import Message
from phospho.models import SentimentObject


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


class PipelineLangsmithRequest(BaseModel):
    project_id: str
    org_id: str
    current_usage: int
    max_usage: Optional[int] = None
    langsmith_api_key: Optional[str] = None
    langsmith_project_name: Optional[str] = None


class PipelineLangfuseRequest(BaseModel):
    project_id: str
    org_id: str
    current_usage: int
    max_usage: Optional[int] = None
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
