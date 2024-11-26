from typing import List, Optional
from pydantic import BaseModel, Field

from phospho_backend.db.models import (
    Project,
    ProjectDataFilters,
)


class Projects(BaseModel):
    projects: List[Project]


class ProjectCreationRequest(BaseModel):
    project_name: str
    settings: Optional[dict] = None


class ProjectUpdateRequest(BaseModel):
    project_name: Optional[str] = None
    # org_id: Optional[str] = None
    settings: Optional[dict] = None


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
    avg_success_rate: Optional[float] = None
    avg_session_length: Optional[float] = None
    total_tokens: Optional[int] = None
    events: Optional[List[UserEventMetadata]] = Field(
        default_factory=List[UserEventMetadata]
    )
    tasks_id: Optional[List[str]] = Field(default_factory=List[str])
    first_message_ts: float
    last_message_ts: float


class Users(BaseModel):
    users: List[UserMetadata]


class FlattenedTasksRequest(BaseModel):
    limit: int = 1000
    with_events: bool = True
    with_sessions: bool = True
    with_removed_events: bool = False


class ComputeJobsRequest(BaseModel):
    job_ids: List[str]
    filters: ProjectDataFilters = Field(default_factory=ProjectDataFilters)


class QuerySessionsTasksRequest(BaseModel):
    filters: ProjectDataFilters = Field(default_factory=ProjectDataFilters)
    limit: Optional[int] = 1000
