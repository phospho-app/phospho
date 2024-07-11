from pydantic import BaseModel, Field
from typing import Optional, List
from app.utils import generate_timestamp

from app.db.models import EventDefinition


class OnboardingSurvey(BaseModel):
    code: Optional[str] = None
    customer: Optional[str] = None
    custom_customer: Optional[str] = None
    contact: Optional[str] = None
    custom_contact: Optional[str] = None


class AddEventsQuery(BaseModel):
    events: List[EventDefinition]


class UploadTasksRequest(BaseModel):
    pd_read_config: dict = Field(default_factory=dict)


class Evaluation_model_definition(BaseModel):
    project_id: str
    system_prompt: str


class Evaluation_model(Evaluation_model_definition):
    created_at: int = Field(default_factory=generate_timestamp)
    removed: bool = False
