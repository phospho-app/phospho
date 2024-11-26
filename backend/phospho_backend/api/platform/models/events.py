from pydantic import BaseModel, Field
from typing import Optional
from phospho.models import ProjectDataFilters


class EventBackfillRequest(BaseModel):
    event_id: str
    filters: ProjectDataFilters = Field(default_factory=ProjectDataFilters)
    sample_rate: float = Field(ge=0, le=1)


class LabelRequest(BaseModel):
    new_label: str


class ScoreRequest(BaseModel):
    new_value: float
