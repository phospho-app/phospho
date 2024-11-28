from phospho.models import ProjectDataFilters
from pydantic import BaseModel, Field

from phospho_backend.db.models import EventDefinition


class OnboardingSurvey(BaseModel):
    code: str | None = None
    customer: str | None = None
    custom_customer: str | None = None
    contact: str | None = None
    custom_contact: str | None = None


class AddEventsQuery(BaseModel):
    events: list[EventDefinition]


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


class EmailClusteringsQuery(BaseModel):
    filters: ProjectDataFilters
