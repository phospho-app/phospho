from typing import Optional, Literal
from pydantic import BaseModel, Field


class FineTuningJobCreationRequest(BaseModel):
    file_id: str
    parameters: Optional[dict] = {}
    model: Optional[str] = "mistralai/Mistral-7B-Instruct-v0.1"
