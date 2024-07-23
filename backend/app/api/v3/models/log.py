from typing import List, Literal
from app.api.v2.models.log import (
    LogEvent,
    LogError,
    LogReply,
)
from pydantic import BaseModel


class MinimalLogEvent(BaseModel, extras="allow"):
    session_id: str
    messages: List[str]
    merge: Literal["replace", "append", "resolve"] = "resolve"


class LogRequest(BaseModel):
    project_id: str
    batched_log_events: List[MinimalLogEvent]
