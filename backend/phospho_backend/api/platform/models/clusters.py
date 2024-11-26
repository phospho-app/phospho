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
    clustering_mode: Literal["agglomerative", "dbscan"] = "agglomerative"
    merge_clusters: Optional[bool] = False
    customer_id: Optional[str] = None
    clustering_id: Optional[str] = None
    clustering_name: Optional[str] = None
    user_email: Optional[str] = None
    scope: Literal["messages", "sessions", "users"] = "messages"
    output_format: Literal[
        "title_description", "user_persona", "question_and_answer"
    ] = "title_description"
    nb_credits_used: int  # Used to bill the organization
