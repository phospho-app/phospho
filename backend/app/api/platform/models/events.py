from pydantic import BaseModel, Field
from typing import Optional


class EventBackfillRequest(BaseModel):
    created_at_start: Optional[float] = None
    created_at_end: Optional[float] = None
    event_id: str
    sample_rate: float = Field(ge=0, le=1)


class LabelRequest(BaseModel):
    new_label: str


class ScoreRequest(BaseModel):
    new_value: float
