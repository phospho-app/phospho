from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from phospho_backend.utils import generate_uuid, generate_timestamp


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
    session_id: Optional[str] = (
        None  # The session id used to generate the embedding, optional
    )


class EmbeddingRequest(BaseModel, extra="allow"):
    input: str | List[str]  # The text used to generate the embedding
    model: Literal[
        "intent-embed"
    ]  # The model used to generate the embedding (a model represent the full piepline and might be user facing, ex: embed-english-v3.0)
    org_id: Optional[str] = None  # Organization identifier, optional
    project_id: str  # Project identifier, optional
    task_id: Optional[str] = (
        None  # The task id (phospho) used to generate the embedding
    )
    nb_credits_used: int  # The number of credits used to generate the embedding


class EmbeddingResponseData(BaseModel):
    object: Literal["embedding"] = "embedding"
    embedding: List[float]  # The embeddings vector
    index: int = 0  # The index of the embedding in the list of embeddings


class EmbeddingUsage(BaseModel):
    prompt_tokens: int
    total_tokens: int  # For the embeddings api, it is equal to prompt_tokens


class EmbeddingResponse(BaseModel):
    """
    Embedding response model
    OpenAI compatible
    """

    object: Literal["list"] = "list"
    data: List[EmbeddingResponseData]
    model: Literal["intent-embed"] = (
        "intent-embed"  # The model used to generate the embedding
    )
    usage: EmbeddingUsage  # The usage of the model, {"prompt_tokens": 8, "total_tokens": 8}
