from typing import Literal, cast

from phospho.models import ProjectDataFilters
from pydantic import BaseModel, Field


class AggregateMetricsRequest(BaseModel):
    index: list[Literal["days", "minutes"]] = Field(
        default_factory=lambda: [cast(Literal["days", "minutes"], "days")]
    )
    columns: list[Literal["event_name", "flag"]] = Field(default_factory=list)
    count_of: Literal["tasks", "events"] | None = "tasks"
    timerange: Literal["last_7_days", "last_30_minutes"] | None = "last_7_days"
    filters: ProjectDataFilters | None = None
    limit: int = 1000


class EventsMetricsFilter(BaseModel):
    pass


class ABTestVersions(BaseModel):
    versionA: str | None
    versionB: str | None
    selected_events_ids: list[str] | None
    filtersA: ProjectDataFilters | None
    filtersB: ProjectDataFilters | None


class ClusteringEmbeddingCloud(BaseModel):
    """
    Represents the request to generate a cloud of embeddings for a clustering
    """

    clustering_id: str
    type: Literal["pca", "tsne"] = "pca"


class DashboardMetricsFilter(BaseModel):
    graph_name: list[str] | None = None


class Pagination(BaseModel):
    page: int = 1
    per_page: int = 10


class Sorting(BaseModel):
    id: str
    desc: bool


class QuerySessionsTasksRequest(BaseModel):
    filters: ProjectDataFilters = Field(default_factory=ProjectDataFilters)
    pagination: Pagination | None = None
    sorting: list[Sorting] | None = None


class QueryUserMetadataRequest(BaseModel):
    filters: ProjectDataFilters = Field(default_factory=ProjectDataFilters)
    pagination: Pagination | None = None
    sorting: list[Sorting] | None = None
    user_id_search: str | None = None


class DetectClustersRequest(BaseModel):
    limit: int | None = None
    filters: ProjectDataFilters | None = Field(default_factory=ProjectDataFilters)
    scope: Literal["messages", "sessions", "users"] = "messages"
    instruction: str | None = "user intent"
    nb_clusters: int | None = None
    clustering_mode: Literal["agglomerative", "dbscan"] = "agglomerative"
    output_format: Literal[
        "title_description", "user_persona", "question_and_answer"
    ] = "title_description"


class FetchClustersRequest(BaseModel):
    clustering_id: str | None = None
    limit: int = 100


class AggregatedSessionsRequest(BaseModel):
    metrics: list[str] = Field(default_factory=list)
    filters: ProjectDataFilters = Field(default_factory=ProjectDataFilters)
    limit: int | None = None


class ClusteringCostRequest(BaseModel):
    scope: Literal["messages", "sessions", "users"] = "messages"
    filters: ProjectDataFilters = Field(default_factory=ProjectDataFilters)
    limit: int | None = None
