from typing import Dict, List, Literal, Optional, Union
from phospho_backend.api.v3.models.run import RoleContentMessage
from pydantic import BaseModel, Field
from phospho_backend.utils import generate_uuid, generate_timestamp


class MinimalLogEventForMessages(BaseModel, extra="allow"):
    session_id: str = Field(default_factory=generate_uuid)
    messages: List[RoleContentMessage] = Field(default_factory=list)
    merge_mode: Literal["resolve", "append", "replace"] = "replace"
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
    batched_log_events: List[MinimalLogEventForMessages]


class LogReply(BaseModel):
    logged_events: List[Union[MinimalLogEventForMessages, LogError]]
