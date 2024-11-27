from pydantic import BaseModel

from phospho_backend.api.v3.models.run import RoleContentMessage
from phospho_backend.db.models import Event

from .log import MinimalLogEvent


class Events(BaseModel):
    events: list[Event]


class DetectEventsInTaskRequest(MinimalLogEvent):
    pass


class DetectEventInMessagesRequest(BaseModel):
    messages: list[RoleContentMessage]


class EventDetectionReply(BaseModel, extra="allow"):
    events: dict[str, list[Event]]
