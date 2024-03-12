from pydantic import BaseModel
from app.db.models import EventDefinition


class AddEventRequest(BaseModel):
    event: EventDefinition


class RemoveEventRequest(BaseModel):
    event_name: str
