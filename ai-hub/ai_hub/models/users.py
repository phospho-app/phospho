from typing import List, Optional

from pydantic import BaseModel, Field

from ai_hub.utils import generate_uuid


class User(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    project_id: str
    org_id: Optional[str] = None  # Organization identifier, optional
    sessions_ids: List[str] = []  # The user's language
