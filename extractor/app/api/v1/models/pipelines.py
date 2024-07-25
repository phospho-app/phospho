from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Literal

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
    events: Dict[str, List[Event]]
    flag: Dict[str, Literal["success", "failure"]]
    language: Dict[str, Optional[str]] = Field(default_factory=dict)
    sentiment: Dict[str, Optional[SentimentObject]] = Field(default_factory=dict)


class RunRecipeOnTaskRequest(BaseModel):
    tasks: List[Task]
    recipe: Recipe


class PipelineOpentelemetryRequest(BaseModel):
    project_id: str
    org_id: str
    current_usage: int
    max_usage: Optional[int] = None
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
