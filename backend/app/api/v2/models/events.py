from typing import List, Optional, Literal
from pydantic import BaseModel
from app.db.models import Event
from .log import MinimalLogEvent


class Events(BaseModel):
    events: List[Event]


class EventDetectionRequest(MinimalLogEvent):
    pass


class EventDetectionReply(EventDetectionRequest):
    events: List[Event]


class PipelineResults(BaseModel):
    events: List[Event]
    flag: Optional[Literal["success", "failure"]]
