from pydantic import BaseModel
from typing import Optional, List

from app.db.models import EventDefinition


class OnboardingSurvey(BaseModel):
    code: str
    customer: str
    custom_customer: Optional[str] = None
    contact: str
    custom_contact: Optional[str] = None


class OnboardingSurveyResponse(BaseModel):
    suggested_events: List[EventDefinition]
    phospho_task_id: Optional[str] = None


class AddEventsQuery(BaseModel):
    events: List[EventDefinition]
