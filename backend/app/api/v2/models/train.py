from pydantic import BaseModel
from typing import Optional, List


class TrainRequest(BaseModel):
    model: str  # Model identifier
    # Either a dataset id or a list of examples should be provided
    dataset: Optional[str] = None  # Dataset identifier or dataset id or file id
    examples: Optional[List[dict]] = (
        None  # A list of examples when no dataset is provided
    )
    # Add a parameter to know if it's a binary classification, multi-class classification or a regression
    task_type: str  # Task identifier: for now, we only support "binary-classification"
    org_id: Optional[str] = None  # Organization identifier, optional
