from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from ai_hub.utils import generate_uuid, generate_timestamp


class Embedding(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    created_at: int = Field(default_factory=generate_timestamp)
    text: str  # The text used to generate the embedding
    embeddings: List[float]  # The embeddings vector
    # The model used to generate the embedding (a model represent the full pipeline and might be user facing, ex: embed-english-v3.0)
    model: Literal["intent-embed", "intent-embed-2", "intent-embed-3"] = (
        "intent-embed-3"
    )
    org_id: Optional[str] = None  # Organization identifier, optional
    project_id: Optional[str] = None  # Project identifier, optional
    task_id: Optional[str] = None
    session_id: Optional[str] = None
    user_id: Optional[str] = None
    scope: Literal["messages", "sessions", "users"] = "messages"
    instruction: Optional[str] = "user intent"


class EmbeddingRequest(BaseModel):
    # The text used to generate the embedding
    text: str
    # The model used to generate the embedding (a model represent the full pipeline and might be user facing, ex: embed-english-v3.0)
    model: Literal["intent-embed", "intent-embed-2", "intent-embed-3"] = (
        "intent-embed-3"
    )
    org_id: str
    project_id: str
    task_id: Optional[str] = None
    session_id: Optional[str] = None
    scope: Literal["messages", "sessions", "users"] = "messages"
    instruction: Optional[str] = "user intent"
