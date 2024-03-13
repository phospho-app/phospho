import datetime

from typing import Any, Dict, List, Literal, Optional, Union
from pydantic import BaseModel, Field

from app.db.models import Project, Event, Task, Session


class Projects(BaseModel):
    projects: List[Project]


class ProjectCreationRequest(BaseModel):
    project_name: str
    settings: Optional[dict] = None


class ProjectUpdateRequest(BaseModel):
    project_name: Optional[str] = None
    # org_id: Optional[str] = None
    settings: Optional[dict] = None


class ProjectTasksFilter(BaseModel):
    """A model to filter tasks by different criteria. All criteria are optional. Criterias are combined with AND."""

    event_name: Optional[Union[str, List[str]]] = Field(
        default=None,
        description="The name of the event. Can be a list of event names. Will only return tasks that have at least an event with this name.",
    )
    flag: Optional[Literal["success", "failure"]] = Field(
        default=None,
        description="The flag of the task. Will only return tasks that have this flag.",
    )
    last_eval_source: Optional[str] = Field(
        default=None,
        description="The source of the eval. Will only return tasks that have their latest_eval with this source.",
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default=None,
        description="A dict of metadata. Will only return tasks that have at least one metadata matching the dict.",
    )
    created_at_start: Optional[Union[int, datetime.datetime]] = Field(
        default=None,
        description="The start of the creation date range. Can be a timestamp or a datetime object. Timestamp is the number of seconds since the epoch (rounded to int). Includes the start.",
    )
    created_at_end: Optional[Union[int, datetime.datetime]] = Field(
        default=None,
        description="The end of the creation date range. Can be a timestamp or a datetime object. Timestamp is the number of seconds since the epoch (rounded to int). Includes the end.",
    )


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
