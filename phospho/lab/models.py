from pydantic import BaseModel, Field
from phospho.utils import generate_timestamp, generate_uuid
from typing import Any, Optional, List, Dict


class Message(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    created_at: int = Field(default_factory=generate_timestamp)
    role: str = "user"
    content: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class JobResult(BaseModel):
    created_at: int = Field(default_factory=generate_timestamp)
    job_name: str
    result_type: str
    value: Any
    logs: List[Any] = Field(default_factory=list)


class JobConfig(BaseModel):
    current_config: Dict[str, Any]
    config_values: Dict[str, List[Any]]
