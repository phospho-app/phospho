from pydantic import BaseModel
from typing import List, Optional

from app.db.models import Task, Recipe
from phospho.lab import Message
from phospho.models import SentimentObject, PipelineResults  # noqa: F401


class BillOnStripeRequest(BaseModel):
    org_id: str
    project_id: str
    nb_job_results: int
    meter_event_name: str = "phospho_usage_based_meter"
    customer_id: Optional[str] = None


class RunMainPipelineOnTaskRequest(BaseModel):
    task: Task
    project_id: str
    org_id: str
    customer_id: Optional[str] = None


class RunMainPipelineOnMessagesRequest(BaseModel):
    project_id: str
    org_id: str
    messages: List[Message]
    customer_id: Optional[str] = None


class RunRecipeOnTaskRequest(BaseModel):
    tasks: Optional[List[Task]] = None
    recipe: Recipe
    customer_id: Optional[str] = None
    org_id: str
    project_id: str
    tasks_ids: Optional[List[str]] = None


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
    customer_id: Optional[str] = None


class PipelineLangfuseRequest(BaseModel):
    project_id: str
    org_id: str
    current_usage: int
    max_usage: Optional[int] = None
    customer_id: Optional[str] = None
