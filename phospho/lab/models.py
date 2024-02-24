from pydantic import BaseModel, Field
from phospho.utils import generate_timestamp, generate_uuid
from typing import Any


class Message(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    content: str


class JobResult(BaseModel):
    created_at: int = Field(default_factory=generate_timestamp)
    job_name: str
    result_type: str
    value: Any
