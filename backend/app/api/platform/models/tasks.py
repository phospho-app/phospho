from typing import Optional
from pydantic import BaseModel
from app.db.models import EventDefinition


class AddEventRequest(BaseModel):
    event: EventDefinition
    score_range_value: Optional[float] = None
    score_category_label: Optional[str] = None


class RemoveEventRequest(BaseModel):
    event_name: str
