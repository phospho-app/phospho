from pydantic import BaseModel
from phospho_backend.db.models import EventDefinition
from typing import Literal, Optional


class AddEventRequest(BaseModel):
    event: EventDefinition


class RemoveEventRequest(BaseModel):
    event_name: str


class SessionHumanEvalRequest(BaseModel):
    human_eval: Optional[Literal["success", "failure"]] = None
    project_id: Optional[str] = None
    source: Optional[str] = "owner"
