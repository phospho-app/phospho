import datetime

from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Union
from app.api.v2.models.projects import ProjectTasksFilter


class ProjectDataFilters(BaseModel):
    created_at_start: Optional[Union[int, datetime.datetime]] = None
    created_at_end: Optional[Union[int, datetime.datetime]] = None
    event_name: Optional[List[str]] = None
    flag: Optional[str] = None
    user_id: Optional[str] = None


class ProjectEventsFilters(BaseModel):
    event_name: Optional[Union[str, List[str]]] = Field(
        None,
        description="The name of the event. Can be a list of event names. Will only return tasks that have at least an event with this name.",
    )
    created_at_start: Optional[Union[int, datetime.datetime]] = Field(
        None,
        description="The start of the creation date range. Can be a timestamp or a datetime object. Timestamp is the number of seconds since the epoch (rounded to int). Includes the start.",
    )
    created_at_end: Optional[Union[int, datetime.datetime]] = Field(
        None,
        description="The end of the creation date range. Can be a timestamp or a datetime object. Timestamp is the number of seconds since the epoch (rounded to int). Includes the end.",
    )


class ProjectSessionsFilters(BaseModel):
    created_at_start: Optional[Union[int, datetime.datetime]] = Field(
        None,
        description="The start of the creation date range. Can be a timestamp or a datetime object. Timestamp is the number of seconds since the epoch (rounded to int). Includes the start.",
    )
    created_at_end: Optional[Union[int, datetime.datetime]] = Field(
        None,
        description="The end of the creation date range. Can be a timestamp or a datetime object. Timestamp is the number of seconds since the epoch (rounded to int). Includes the end.",
    )


class AggregateMetricsRequest(BaseModel):
    index: Optional[List[str]] = Field(default_factory=lambda: ["days"])
    columns: Optional[List[str]] = Field(default_factory=list)
    count_of: Optional[str] = "tasks"
    timerange: Optional[str] = "last_7_days"
    tasks_filter: Optional[ProjectTasksFilter] = None
    events_filter: Optional[ProjectEventsFilters] = None
    limit: int = 1000


class TasksMetricsFilter(BaseModel):
    flag: Optional[Literal["success", "failure"]] = Field(
        default=None,
        description="The flag of the task. Will only return tasks that have this flag.",
    )
    event_name: Optional[Union[str, List[str]]] = Field(
        default=None,
        description="The name of the event. Can be a list of event names. Will only return tasks that have at least an event with this name.",
    )


class SessionsMetricsFilter(BaseModel):
    event_name: Optional[Union[str, List[str]]] = Field(
        default=None,
        description="The name of the event. Can be a list of event names. Will only return tasks that have at least an event with this name.",
    )


class EventsMetricsFilter(BaseModel):
    pass


class DashboardMetricsFilter(BaseModel):
    graph_name: Optional[List[str]] = None


class Pagination(BaseModel):
    page: int = 1
    per_page: int = 10


class Sorting(BaseModel):
    id: str
    desc: bool


class QuerySessionsTasksRequest(BaseModel):
    filters: ProjectDataFilters = Field(default_factory=ProjectDataFilters)
    pagination: Pagination = Field(default_factory=Pagination)
    sorting: Optional[List[Sorting]] = None
