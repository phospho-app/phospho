from pydantic import BaseModel, Field
from typing import List, Literal, Optional
from phospho.models import Cluster, Clustering, ProjectDataFilters


class Clusters(BaseModel):
    clusters: List[Cluster]


class Clusterings(BaseModel):
    clusterings: List[Clustering]


class ClusteringRequest(BaseModel):
    model: Literal[
        "intent-embed",
        "intent-embed-2",
        "intent-embed-3",
    ] = "intent-embed-3"
    project_id: str  # Project identifier
    org_id: str
    limit: Optional[int] = None  # Limit of tasks to be clustered, None means no limit
    filters: ProjectDataFilters = Field(default_factory=ProjectDataFilters)
    instruction: Optional[str] = "user intent"
    nb_clusters: Optional[int] = None
    clustering_mode: Literal["Agglomerative", "DBSCAN"] = "Agglomerative"
    merge_clusters: Optional[bool] = False
    customer_id: Optional[str] = None
    nb_credits_used: int
    clustering_id: Optional[str] = None
    clustering_name: Optional[str] = None
