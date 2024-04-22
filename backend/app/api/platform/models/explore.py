from pydantic import BaseModel, Field
from typing import List, Literal, Optional, Union
from phospho.models import ProjectDataFilters


class AggregateMetricsRequest(BaseModel):
    index: Optional[List[str]] = Field(default_factory=lambda: ["days"])
    columns: Optional[List[str]] = Field(default_factory=list)
    count_of: Optional[str] = "tasks"
    timerange: Optional[str] = "last_7_days"
    filters: Optional[ProjectDataFilters] = None
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
    pagination: Optional[Pagination] = None
    sorting: Optional[List[Sorting]] = None
