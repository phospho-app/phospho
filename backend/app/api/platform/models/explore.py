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
