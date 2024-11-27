from pydantic import BaseModel

from phospho_backend.db.models import Session


class Sessions(BaseModel):
    sessions: list[Session]


class SessionCreationRequest(BaseModel):
    project_id: str
    data: dict | None = None


class SessionUpdateRequest(BaseModel):
    metadata: dict | None = None
    data: dict | None = None
    preview: str | None = None
    notes: str | None = None
