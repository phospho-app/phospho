from pydantic import BaseModel, Field
from typing import Optional


class EventBackfillRequest(BaseModel):
    created_at_start: Optional[int]
    created_at_end: Optional[int]
    event_id: str
    sample_rate: float = Field(ge=0, le=1)
