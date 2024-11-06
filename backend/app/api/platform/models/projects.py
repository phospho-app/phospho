from pydantic import BaseModel, Field
from typing import Optional, List

from app.db.models import EventDefinition
from phospho.models import ProjectDataFilters


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


class ConnectLangsmithQuery(BaseModel):
    langsmith_api_key: str
    langsmith_project_name: str


class ConnectLangfuseQuery(BaseModel):
    langfuse_secret_key: str
    langfuse_public_key: str


class EmailUsersQuery(BaseModel):
    filters: ProjectDataFilters
