from typing import Literal
from phospho_backend.api.v3.models.run import RoleContentMessage
from pydantic import BaseModel, Field
from phospho_backend.utils import generate_uuid, generate_timestamp


class MinimalLogEventForMessages(BaseModel, extra="allow"):
    session_id: str = Field(default_factory=generate_uuid)
    messages: list[RoleContentMessage] = Field(default_factory=list)
    merge_mode: Literal["resolve", "append", "replace"] = "replace"
    created_at: int = Field(default_factory=generate_timestamp)
    metadata: dict[str, object] | None = None
    version_id: str | None = None
    user_id: str | None = None
    flag: Literal["success", "failure"] | None = None
    test_id: str | None = None


class LogError(BaseModel):
    error_in_log: str


class LogRequest(BaseModel):
    project_id: str
    batched_log_events: list[MinimalLogEventForMessages]


class LogReply(BaseModel):
    logged_events: list[MinimalLogEventForMessages | LogError]
