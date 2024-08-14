from typing import List, Optional, Literal, Dict, Any
from pydantic import BaseModel, Field
from app.core import config

from app.db.models import (
    Project,
    Event,
    Session,
    ProjectDataFilters,
    EventDefinition,  # noqa: F401
)


class Projects(BaseModel):
    projects: List[Project]


class ProjectCreationRequest(BaseModel):
    project_name: str
    settings: Optional[dict] = None


class ProjectUpdateRequest(BaseModel):
    project_name: Optional[str] = None
    # org_id: Optional[str] = None
    settings: Optional[dict] = None


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
    with_removed_events: bool = False


class ComputeJobsRequest(BaseModel):
    job_ids: List[str]
    filters: ProjectDataFilters = Field(default_factory=ProjectDataFilters)


class QuerySessionsTasksRequest(BaseModel):
    filters: ProjectDataFilters = Field(default_factory=ProjectDataFilters)


class AnalyticsQueryRequest(BaseModel):
    """Represents an analytics query request without the project_id field."""

    collection: Literal[
        "events",
        "job_results",
        "clusters",  #
        "embeddings",  #
        "sessions",
        "tasks",
    ]
    aggregation_operation: Literal["count", "sum", "avg", "min", "max"] = Field(
        ...,
        description="The aggregation opperation to perform. If the method is different than count, the `aggregation_field` is required.",
    )
    aggregation_field: Optional[str] = Field(
        default=None,
        description="The field to aggregate on. Not required for count.",
    )  # Not required for count
    dimensions: Optional[List[str]] = Field(
        default_factory=list,
        description="The dimensions to group by (e.g., flag, metadata.model, ...). Can be `month`, `day`, `hour`, or`minute`, which will be computed from the created_at field.",
    )
    filters: Optional[dict] = Field(
        default_factory=dict,
        description='Optional filters to apply, passed in MongoDB query format if need be (e.g., {"created_at": {"$gte": 1723218277}})',
    )
    sort: Optional[Dict[str, int]] = Field(
        default_factory=dict,
        description='Optional sorting criteria (e.g., {"date": 1} for ascending, {"date": -1} for descending)',
    )
    limit: Optional[int] = Field(
        2000,
        description=f"Limit on the number or rows returned. Cannot exceed {config.QUERY_MAX_LEN_LIMIT} records.",
    )
    # Optional parameters for the query service
    filter_out_null_values: Optional[bool] = Field(
        False, description="Filter out null values from the result series."
    )

    # Let's provide an example of a query
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "collection": "tasks",
                    "aggregation_operation": "count",
                    "dimensions": ["minute", "environment"],
                    "filters": {"created_at": {"$gte": 1723218277}},
                    "sort": {"date": 1},
                    "limit": 2000,
                }
            ]
        }
    }


class AnalyticsQueryResponse(BaseModel):
    """
    Response model for the analytics query endpoint.
    """

    result: List[Dict[str, Any]]

    # Let's provide an example of a query
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "result": [
                        {
                            "value": 1,
                            "minute": "2024-08-12 21:59",
                            "environment": "default environment",
                        },
                        {
                            "value": 1,
                            "minute": "2024-08-11 08:43",
                            "environment": "default environment",
                        },
                        {
                            "value": 1,
                            "minute": "2024-08-11 19:14",
                            "environment": "default environment",
                        },
                        {
                            "value": 1,
                            "minute": "2024-08-11 19:01",
                            "environment": "default environment",
                        },
                        {
                            "value": 1,
                            "minute": "2024-08-10 15:45",
                            "environment": "default environment",
                        },
                    ]
                }
            ]
        }
    }
