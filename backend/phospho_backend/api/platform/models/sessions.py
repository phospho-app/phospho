from pydantic import BaseModel
from phospho_backend.db.models import EventDefinition
from typing import Literal


class AddEventRequest(BaseModel):
    event: EventDefinition


class RemoveEventRequest(BaseModel):
    event_name: str


class SessionHumanEvalRequest(BaseModel):
    human_eval: Literal["success", "failure"] | None = None
    project_id: str | None = None
    source: str | None = "owner"
