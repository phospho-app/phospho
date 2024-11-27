from typing import Literal

from phospho.models import Cluster, Clustering, ProjectDataFilters
from pydantic import BaseModel, Field


class Clusters(BaseModel):
    clusters: list[Cluster]


class Clusterings(BaseModel):
    clusterings: list[Clustering]


class ClusteringRequest(BaseModel):
    model: Literal[
        "intent-embed",
        "intent-embed-2",
        "intent-embed-3",
    ] = "intent-embed-3"
    project_id: str  # Project identifier
    org_id: str
    limit: int | None = None  # Limit of tasks to be clustered, None means no limit
    filters: ProjectDataFilters = Field(default_factory=ProjectDataFilters)
    instruction: str | None = "user intent"
    nb_clusters: int | None = None
    clustering_mode: Literal["agglomerative", "dbscan"] = "agglomerative"
    merge_clusters: bool | None = False
    customer_id: str | None = None
    clustering_id: str | None = None
    clustering_name: str | None = None
    user_email: str | None = None
    scope: Literal["messages", "sessions", "users"] = "messages"
    output_format: Literal[
        "title_description", "user_persona", "question_and_answer"
    ] = "title_description"
    nb_credits_used: int  # Used to bill the organization
