from typing import Dict, List

from pydantic import BaseModel

from phospho_backend.api.v3.models.run import RoleContentMessage
from phospho_backend.db.models import Event

from .log import MinimalLogEvent


class Events(BaseModel):
    events: List[Event]


class DetectEventsInTaskRequest(MinimalLogEvent):
    pass


class DetectEventInMessagesRequest(BaseModel):
    messages: List[RoleContentMessage]


class EventDetectionReply(BaseModel, extra="allow"):
    events: Dict[str, List[Event]]
