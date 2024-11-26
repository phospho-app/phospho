from typing import List, Optional
from pydantic import BaseModel
from phospho_backend.db.models import Session


class Sessions(BaseModel):
    sessions: List[Session]


class SessionCreationRequest(BaseModel):
    project_id: str
    data: Optional[dict] = None


class SessionUpdateRequest(BaseModel):
    metadata: Optional[dict] = None
    data: Optional[dict] = None
    preview: Optional[str] = None
    notes: Optional[str] = None
