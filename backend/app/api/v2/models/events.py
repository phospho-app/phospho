from typing import List
from pydantic import BaseModel
from app.db.models import Event


class Events(BaseModel):
    events: List[Event]
