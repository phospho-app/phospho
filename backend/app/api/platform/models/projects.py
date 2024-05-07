from pydantic import BaseModel
from typing import Optional, List

from app.db.models import EventDefinition


class OnboardingSurvey(BaseModel):
    code: Optional[str] = None
    customer: Optional[str] = None
    custom_customer: Optional[str] = None
    contact: Optional[str] = None
    custom_contact: Optional[str] = None


class AddEventsQuery(BaseModel):
    events: List[EventDefinition]
