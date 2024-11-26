from pydantic import BaseModel, Field
from typing import List, Literal, Optional, cast
from phospho.models import ProjectDataFilters


class AggregateMetricsRequest(BaseModel):
    index: List[Literal["days", "minutes"]] = Field(
        default_factory=lambda: [cast(Literal["days", "minutes"], "days")]
    )
    columns: List[Literal["event_name", "flag"]] = Field(default_factory=list)
    count_of: Optional[Literal["tasks", "events"]] = "tasks"
    timerange: Optional[Literal["last_7_days", "last_30_minutes"]] = "last_7_days"
    filters: Optional[ProjectDataFilters] = None
    limit: int = 1000


class EventsMetricsFilter(BaseModel):
    pass


class ABTestVersions(BaseModel):
    versionA: Optional[str]
    versionB: Optional[str]
    selected_events_ids: Optional[List[str]]
    filtersA: Optional[ProjectDataFilters]
    filtersB: Optional[ProjectDataFilters]


class ClusteringEmbeddingCloud(BaseModel):
    """
    Represents the request to generate a cloud of embeddings for a clustering
    """

    clustering_id: str
    type: Literal["pca", "tsne"] = "pca"


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


class QueryUserMetadataRequest(BaseModel):
    filters: ProjectDataFilters = Field(default_factory=ProjectDataFilters)
    pagination: Optional[Pagination] = None
    sorting: Optional[List[Sorting]] = None
    user_id_search: Optional[str] = None


class DetectClustersRequest(BaseModel):
    limit: Optional[int] = None
    filters: Optional[ProjectDataFilters] = Field(default_factory=ProjectDataFilters)
    scope: Literal["messages", "sessions", "users"] = "messages"
    instruction: Optional[str] = "user intent"
    nb_clusters: Optional[int] = None
    clustering_mode: Literal["agglomerative", "dbscan"] = "agglomerative"
    output_format: Literal[
        "title_description", "user_persona", "question_and_answer"
    ] = "title_description"


class FetchClustersRequest(BaseModel):
    clustering_id: Optional[str] = None
    limit: int = 100


class AggregatedSessionsRequest(BaseModel):
    metrics: List[str] = Field(default_factory=list)
    filters: ProjectDataFilters = Field(default_factory=ProjectDataFilters)
    limit: Optional[int] = None


class ClusteringCostRequest(BaseModel):
    scope: Literal["messages", "sessions", "users"] = "messages"
    filters: ProjectDataFilters = Field(default_factory=ProjectDataFilters)
    limit: Optional[int] = None
