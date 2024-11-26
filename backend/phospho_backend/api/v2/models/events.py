from typing import List, Dict
from pydantic import BaseModel
from phospho_backend.db.models import Event
from phospho.models import Message
from .log import MinimalLogEvent


class Events(BaseModel):
    events: List[Event]


class DetectEventsInTaskRequest(MinimalLogEvent):
    pass


class DetectEventInMessagesRequest(BaseModel):
    messages: List[Message]


class EventDetectionReply(BaseModel, extra="allow"):
    events: Dict[str, List[Event]]
