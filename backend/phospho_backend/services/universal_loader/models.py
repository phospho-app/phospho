from pydantic import BaseModel


class OpenAIDatasetFormat(BaseModel):
    content: str | None
    role: str | None
    created_at: str | None
    conversation_id: str | None
    user_id: str | None


class PhosphoDatasetFormat(BaseModel):
    input: str | None
    output: str | None
    created_at: str | None
    task_id: str | None
    session_id: str | None
    user_id: str | None


class UserAssistant(BaseModel):
    user: str | None
    assistant: str | None
