from typing import Literal
from pydantic import BaseModel


class TriggerClusteringRequest(BaseModel):
    project_id: str
    limit: int = 1000
    scope: Literal["messages", "sessions", "users"] = "sessions"
