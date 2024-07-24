from typing import Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field
from app.utils import generate_uuid, generate_timestamp


class MinimalLogEvent(BaseModel, extras="allow"):
    """
    This is the
    """

    session_id: str = Field(default_factory=lambda: generate_uuid("session_"))
    messages: List[str] = Field(default_factory=list)
    merge_mode: Literal["resolve", "append", "replace"] = "resolve"
    created_at: int = Field(default_factory=generate_timestamp)
    metadata: Optional[Dict[str, object]] = None
    version_id: Optional[str] = None
    user_id: Optional[str] = None
    flag: Optional[Literal["success", "failure"]] = None
    test_id: Optional[str] = None


class LogError(BaseModel):
    error_in_log: str


class LogRequest(BaseModel):
    project_id: str
    batched_log_events: List[MinimalLogEvent]


class LogReply(BaseModel):
    logged_events: List[Union[MinimalLogEvent, LogError]]
