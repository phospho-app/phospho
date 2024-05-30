from typing import Optional
from pydantic import BaseModel, Field


class ClusteringRequest(BaseModel):
    project_id: str  # Project identifier, optional
    limit: Optional[int] = Field(
        default=2000, description="Limit the number of messages, defaults to 2000"
    )
