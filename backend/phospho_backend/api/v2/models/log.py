from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Union, Literal
from phospho_backend.utils import generate_uuid, generate_timestamp


class MinimalLogEvent(BaseModel, extra="allow"):
    # This is the minimal log event
    project_id: Optional[str] = None
    input: str
    output: Optional[str] = None


class LogRequest(BaseModel):
    batched_log_events: List[MinimalLogEvent]


class LogEvent(MinimalLogEvent, extra="allow"):
    # Optional fields
    client_created_at: int = Field(default_factory=generate_timestamp)
    created_at: Optional[int] = None
    last_update: Optional[int] = None
    # metadata
    metadata: Optional[Dict[str, object]] = Field(default_factory=Dict[str, object])
    session_id: Optional[str] = None
    task_id: str = Field(default_factory=generate_uuid)
    step_id: Optional[str] = None
    version_id: Optional[str] = None
    user_id: Optional[str] = None
    flag: Optional[Literal["success", "failure"]] = None
    # Testing
    test_id: Optional[str] = None
    # input
    raw_input: Optional[
        Union[
            Dict[str, object],
            str,
            List[Dict[str, object]],
            List[str],
        ]
    ] = None
    raw_input_type_name: Optional[str] = None
    # output
    raw_output: Optional[
        Union[
            Dict[str, object],
            str,
            List[Optional[Dict[str, object]]],
            List[Optional[str]],
        ]
    ] = None
    raw_output_type_name: Optional[str] = None
    # data
    environment: str = "default environment"


class LogError(BaseModel):
    error_in_log: str


class LogReply(BaseModel):
    logged_events: List[Union[LogEvent, LogError]]
