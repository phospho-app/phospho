from typing import Optional
from pydantic import BaseModel


class OpenAI_Dataset_Format(BaseModel):
    content: Optional[str]
    role: Optional[str]
    created_at: Optional[str]
    conversation_id: Optional[str]


class Phospho_Dataset_Format(BaseModel):
    input: Optional[str]
    output: Optional[str]
    created_at: Optional[str]
    task_id: Optional[str]
    session_id: Optional[str]


class User_assistant(BaseModel):
    user: Optional[str]
    assistant: Optional[str]
