from pydantic import BaseModel
from typing import List, Optional

from extractor.db.models import Task, Recipe
from phospho.models import SentimentObject, PipelineResults  # noqa: F401


class RoleContentMessage(BaseModel):
    role: str
    content: str


class ExtractorBaseClass(BaseModel, extra="allow"):
    org_id: str
    project_id: str
    customer_id: Optional[str] = None
    current_usage: int
    max_usage: Optional[int] = None


class BillOnStripeRequest(ExtractorBaseClass):
    nb_job_results: int
    meter_event_name: str = "phospho_usage_based_meter"
    recipe_type: Optional[str] = None


class RunMainPipelineOnTaskRequest(ExtractorBaseClass):
    task: Task


class RunMainPipelineOnMessagesRequest(ExtractorBaseClass):
    messages: List[RoleContentMessage]


class RunRecipeOnTaskRequest(ExtractorBaseClass):
    tasks: Optional[List[Task]] = None
    recipe: Recipe
    tasks_ids: Optional[List[str]] = None


class PipelineOpentelemetryRequest(ExtractorBaseClass):
    open_telemetry_data: dict


class PipelineLangsmithRequest(ExtractorBaseClass):
    langsmith_api_key: Optional[str] = None
    langsmith_project_name: Optional[str] = None


class PipelineLangfuseRequest(ExtractorBaseClass):
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
