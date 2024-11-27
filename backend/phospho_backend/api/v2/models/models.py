from typing import Literal

from pydantic import BaseModel, Field

from phospho_backend.utils import generate_timestamp


class Model(BaseModel):
    id: str  # Model identifier, also used in the HuggingFace model hub
    created_at: int = Field(default_factory=generate_timestamp)
    status: Literal["training", "trained", "failed", "deleted"]  # Model status
    owned_by: str | None = None  # Owner identifier: phospho or org_id
    task_type: str | None = (
        None  # Task identifier, for won we only support "binary-classification"
    )
    context_window: int | None = None  # Context window size of the model, in tokens


class ModelsResponse(BaseModel):
    models: list  # List of models objects
