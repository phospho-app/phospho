from typing import Dict, List, Optional
from pydantic import BaseModel
from app.db.models import EventDefinition


class AddEventRequest(BaseModel):
    event: EventDefinition
    score_range_value: Optional[float] = None
    score_category_label: Optional[str] = None


class RemoveEventRequest(BaseModel):
    event_name: str


class FetchSpansRequest(BaseModel):
    task_id: str
    project_id: str


class TaskSpans(BaseModel):
    task_id: str
    project_id: str
    spans: List[Dict[str, object]]
