from typing import Optional
from pydantic import BaseModel


class OpenAIDatasetFormat(BaseModel):
    content: Optional[str]
    role: Optional[str]
    created_at: Optional[str]
    conversation_id: Optional[str]
    user_id: Optional[str]


class PhosphoDatasetFormat(BaseModel):
    input: Optional[str]
    output: Optional[str]
    created_at: Optional[str]
    task_id: Optional[str]
    session_id: Optional[str]
    user_id: Optional[str]


class UserAssistant(BaseModel):
    user: Optional[str]
    assistant: Optional[str]
