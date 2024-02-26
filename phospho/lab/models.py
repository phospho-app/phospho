from pydantic import BaseModel, Field
from phospho.utils import generate_timestamp, generate_uuid
from typing import Any, Optional, List
from enum import Enum


class Message(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    created_at: int = Field(default_factory=generate_timestamp)
    role: str = "user"
    content: str
    session_id: Optional[str] = None
    user_id: Optional[str] = None


class ResultType(Enum):
    error = "error"
    bool = "bool"
    literal = "literal"


class JobResult(BaseModel):
    created_at: int = Field(default_factory=generate_timestamp)
    job_name: str
    result_type: ResultType
    value: Any
    logs: List[Any] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
