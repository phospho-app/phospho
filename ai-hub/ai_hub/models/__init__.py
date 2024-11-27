from typing import Literal, Optional

from pydantic import BaseModel, Field

from ai_hub.utils import generate_timestamp


class Model(BaseModel):
    id: str  # Model identifier, also used in the HuggingFace model hub
    created_at: int = Field(default_factory=generate_timestamp)
    status: Literal["training", "trained", "failed", "deleted"]  # Model status
    owned_by: Optional[str] = None  # Owner identifier: phospho or org_id
    task_type: Optional[str] = (
        None  # Task identifier, for won we only support "binary-classification"
    )
    context_window: Optional[int] = None  # Context window size of the model, in tokens
