from pydantic import BaseModel, Field
from phospho.utils import generate_timestamp, generate_uuid
from typing import Any, Optional, List, Dict, Literal


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


class EmptyConfig(BaseModel):
    pass


# Custom configuration class for our implementation of the lab
# If you wish not to use any config, you can use the EmptyConfig class
# You need to pass default values for each parameter
class JobConfig(BaseModel):
    pass


### CUSTOM MODELS ##


class EventDetectionConfig(JobConfig):
    model: Literal["gpt-4", "gpt-3.5-turbo"] = "gpt-4"  # OpenAI model name
    # instruction: str


class EvalConfig(JobConfig):
    model: Literal["gpt-4", "gpt-3.5-turbo"] = "gpt-4"  # OpenAI model name
