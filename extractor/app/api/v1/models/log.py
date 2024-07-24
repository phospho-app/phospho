from typing import Dict, List, Literal, Optional, Union

from app.utils import generate_timestamp, generate_uuid
from pydantic import BaseModel, Field


class MinimalLogEventForTasks(BaseModel, extra="allow"):
    # This is the minimal log event
    project_id: Optional[str] = None
    input: str
    output: Optional[str] = None


class LogEventForTasks(MinimalLogEventForTasks, extra="allow"):
    # Optional fields
    client_created_at: int = Field(default_factory=generate_timestamp)
    created_at: Optional[int] = None
    last_update: Optional[int] = None
    # metadata
    metadata: Optional[Dict[str, object]] = Field(default_factory=dict)
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
    # Backcompute
    job_ids: Optional[List[str]] = None


class LogProcessRequestForTasks(BaseModel):
    logs_to_process: List[LogEventForTasks]
    extra_logs_to_save: List[LogEventForTasks]
    project_id: str
    org_id: str


class MinimalLogEventForMessages(BaseModel, extras="allow"):
    session_id: str
    messages: List[str]
    merge_mode: Literal["resolve", "append", "replace"] = "resolve"
    created_at: int = Field(default_factory=generate_timestamp)
    metadata: Optional[Dict[str, object]] = None
    version_id: Optional[str] = None
    user_id: Optional[str] = None
    flag: Optional[Literal["success", "failure"]] = None
    test_id: Optional[str] = None


class LogProcessRequestForMessages(BaseModel):
    logs_to_process: List[MinimalLogEventForMessages]
    extra_logs_to_save: List[MinimalLogEventForMessages]
    project_id: str
    org_id: str
