from typing import List, Optional
from pydantic import BaseModel, Field

from app.db.models import (
    Project,
    Event,
    Task,
    Session,
    EventDefinition,
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
    events: Optional[List[Event]] = Field(default_factory=list)
    tasks_id: Optional[List[str]] = Field(default_factory=list)
    sessions: Optional[List[Session]] = Field(default_factory=list)


class Users(BaseModel):
    users: List[UserMetadata]


class FlattenedTasksRequest(BaseModel):
    limit: int = 1000
    with_events: bool = True
    with_sessions: bool = True
