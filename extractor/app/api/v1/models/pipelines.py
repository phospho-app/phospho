from pydantic import BaseModel
from typing import List, Optional

from app.db.models import Task, Recipe
from phospho.lab import Message
from phospho.models import SentimentObject, PipelineResults  # noqa: F401


class RunMainPipelineOnTaskRequest(BaseModel):
    task: Task


class RunMainPipelineOnMessagesRequest(BaseModel):
    project_id: str
    org_id: str
    messages: List[Message]


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
