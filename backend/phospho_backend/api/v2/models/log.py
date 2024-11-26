from pydantic import BaseModel, Field
from typing import Literal
from phospho_backend.utils import generate_uuid, generate_timestamp


class MinimalLogEvent(BaseModel, extra="allow"):
    # This is the minimal log event
    project_id: str | None = None
    input: str
    output: str | None = None


class LogRequest(BaseModel):
    batched_log_events: list[MinimalLogEvent]


class LogEvent(MinimalLogEvent, extra="allow"):
    # Optional fields
    client_created_at: int = Field(default_factory=generate_timestamp)
    created_at: int | None = None
    last_update: int | None = None
    # metadata
    metadata: dict[str, object] | None = Field(default_factory=dict[str, object])
    session_id: str | None = None
    task_id: str = Field(default_factory=generate_uuid)
    step_id: str | None = None
    version_id: str | None = None
    user_id: str | None = None
    flag: Literal["success", "failure"] | None = None
    # Testing
    test_id: str | None = None
    # input
    raw_input: None | (
        dict[str, object] | str | list[dict[str, object]] | list[str]
    ) = None
    raw_input_type_name: str | None = None
    # output
    raw_output: None | (
        dict[str, object] | str | list[dict[str, object] | None] | list[str | None]
    ) = None
    raw_output_type_name: str | None = None
    # data
    environment: str = "default environment"


class LogError(BaseModel):
    error_in_log: str


class LogReply(BaseModel):
    logged_events: list[LogEvent | LogError]
