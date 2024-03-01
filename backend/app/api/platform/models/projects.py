from pydantic import BaseModel
from typing import Optional, List

from app.db.models import EventDefinition


class OnboardingSurvey(BaseModel):
    build: str
    custom_build: Optional[str] = None
    purpose: str
    custom_purpose: Optional[str] = None


class OnboardingSurveyResponse(BaseModel):
    suggested_events: List[EventDefinition]
    phospho_task_id: Optional[str] = None


class AddEventsQuery(BaseModel):
    events: List[EventDefinition]
