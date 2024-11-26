from pydantic import BaseModel, Field
from typing import Any, Dict, List, Literal, Optional
from ai_hub.utils import generate_uuid, generate_timestamp
from phospho.models import ProjectDataFilters
from phospho.utils import generate_version_id


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
    merge_clusters: Optional[bool] = False
    customer_id: Optional[str] = None
    nb_credits_used: int
    clustering_mode: Literal[
        "agglomerative",
        "dbscan",
    ] = "agglomerative"
    clustering_id: Optional[str] = None
    clustering_name: Optional[str] = None
    user_email: Optional[str] = None
    scope: Literal[
        "messages",
        "sessions",
        "users",
    ] = "messages"
    output_format: Literal[
        "title_description",
        "user_persona",
        "question_and_answer",
    ] = "title_description"


class Clustering(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    org_id: Optional[str] = None  # Organization identifier, optional
    project_id: Optional[str] = None  # Project identifier
    name: Optional[str] = Field(default_factory=generate_version_id)
    created_at: int = Field(default_factory=generate_timestamp)
    model: Literal[
        "intent-embed",
        "intent-embed-2",
        "intent-embed-3",
    ] = "intent-embed-3"
    type: Optional[str] = None
    nb_clusters: Optional[int] = None
    clusters_ids: List[str]  # reference to the clusters
    # status tracking
    status: Optional[Literal["started", "summaries", "completed"]] = None
    percent_of_completion: Optional[float] = None
    filters: Optional[ProjectDataFilters] = ProjectDataFilters()
    # On what data the clustering is done
    scope: Literal["messages", "sessions", "users"] = "messages"
    instruction: Optional[str] = "user intent"
    pca: Dict[str, Any] = {}


class Cluster(BaseModel):
    model: Literal[
        "intent-embed",
        "intent-embed-2",
        "intent-embed-3",
    ] = "intent-embed-3"
    id: str = Field(default_factory=generate_uuid)
    created_at: int = Field(default_factory=generate_timestamp)
    org_id: Optional[str] = None  # Organization identifier, optional
    project_id: Optional[str] = None  # Project identifier
    clustering_id: str  # Clustering identifier, optional
    name: Optional[str] = None
    description: Optional[str] = None
    # $size of tasks_id + sessions_id
    size: int
    # reference to the data in the cluster
    tasks_ids: Optional[List[str]] = None
    sessions_ids: Optional[List[str]] = None
    users_ids: Optional[List[str]] = None
    scope: Literal["messages", "sessions", "users"] = "messages"
    instruction: Optional[str] = "user intent"
    embeddings_ids: Optional[List[str]] = None
