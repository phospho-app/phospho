from typing import List, Optional, Literal
from pydantic import BaseModel
from app.db.models import Event
from phospho.lab.models import Message
from .log import MinimalLogEvent


class Events(BaseModel):
    events: List[Event]


class DetectEventsInTaskRequest(MinimalLogEvent):
    pass


class DetectEventInMessagesRequest(BaseModel):
    messages: List[Message]


class EventDetectionReply(BaseModel, extra="allow"):
    events: List[Event]


class PipelineResults(BaseModel):
    events: List[Event]
    flag: Optional[Literal["success", "failure"]]
