from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from app.utils import generate_uuid, generate_timestamp


class Embedding(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    created_at: int = Field(default_factory=generate_timestamp)
    text: str  # The text used to generate the embedding
    embeddings: List[float]  # The embeddings vector
    model: str  # The model used to generate the embedding (a model represent the full piepline and might be user facing, ex: embed-english-v3.0)
    org_id: Optional[str] = None  # Organization identifier, optional
    project_id: Optional[str] = None  # Project identifier, optional
    task_id: Optional[str] = (
        None  # The task id (phospho) used to generate the embedding, optional
    )


class EmbeddingRequest(BaseModel):
    input: str  # The text used to generate the embedding
    model: str  # The model used to generate the embedding (a model represent the full piepline and might be user facing, ex: embed-english-v3.0)
    org_id: Optional[str] = None  # Organization identifier, optional
    project_id: Optional[str] = None  # Project identifier, optional
    task_id: Optional[str] = (
        None  # The task id (phospho) used to generate the embedding
    )
