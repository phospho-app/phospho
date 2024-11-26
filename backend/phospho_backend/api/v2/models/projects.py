from pydantic import BaseModel, Field

from phospho_backend.db.models import (
    Project,
    ProjectDataFilters,
)


class Projects(BaseModel):
    projects: list[Project]


class ProjectCreationRequest(BaseModel):
    project_name: str
    settings: dict | None = None


class ProjectUpdateRequest(BaseModel):
    project_name: str | None = None
    # org_id: Optional[str] = None
    settings: dict | None = None


class UserEventMetadata(BaseModel):
    event_name: str
    count: int


class UserMetadata(BaseModel):
    """
    The representation of a end-user of an app.
    This is not a Propellauth user (of phospho).
    """

    user_id: str
    nb_tasks: int
    avg_success_rate: float | None = None
    avg_session_length: float | None = None
    total_tokens: int | None = None
    events: list[UserEventMetadata] | None = Field(
        default_factory=list[UserEventMetadata]
    )
    tasks_id: list[str] | None = Field(default_factory=list[str])
    first_message_ts: float
    last_message_ts: float


class Users(BaseModel):
    users: list[UserMetadata]


class FlattenedTasksRequest(BaseModel):
    limit: int = 1000
    with_events: bool = True
    with_sessions: bool = True
    with_removed_events: bool = False


class ComputeJobsRequest(BaseModel):
    job_ids: list[str]
    filters: ProjectDataFilters = Field(default_factory=ProjectDataFilters)


class QuerySessionsTasksRequest(BaseModel):
    filters: ProjectDataFilters = Field(default_factory=ProjectDataFilters)
    limit: int | None = 1000
