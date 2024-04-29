from pydantic import BaseModel
from typing import Optional


class TrainRequest(BaseModel):
    model: str  # Model identifier
    dataset: str  # Dataset identifier or dataset id or file id
    # Add a parameter to know if it's a binary classification, multi-class classification or a regression
    task_type: str  # Task identifier: for now, we only support "binary-classification"
    org_id: Optional[str] = None  # Organization identifier, optional
