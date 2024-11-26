from pydantic import BaseModel
from phospho_backend.db.models import EventDefinition
from phospho_backend.services.integrations.opentelemetry import StandardSpanModel


class AddEventRequest(BaseModel):
    event: EventDefinition
    score_range_value: float | None = None
    score_category_label: str | None = None


class RemoveEventRequest(BaseModel):
    event_name: str


class FetchSpansRequest(BaseModel):
    task_id: str
    project_id: str


class TaskSpans(BaseModel):
    task_id: str
    project_id: str
    spans: list[StandardSpanModel]
