from typing import Literal, Optional
from pydantic import BaseModel, Field
from phospho.models import ProjectDataFilters


class MetadataValueResponse(BaseModel):
    value: Optional[float]


class MetadataPivotResponse(BaseModel):
    """
    List of dictionaries, each containing:
    - breakdown_by: str
    - metric: float
    - stack: Dict[str, float] (only for "tags_distribution") containing the event_name and its count

    The output stack can be used to create a stacked bar chart.
    """

    pivot_table: list


class MetadataPivotQuery(BaseModel):
    """
    The metric can be one of the following:
    - "sum": Sum of the metadata field
    - "avg": Average of the metadata field
    - "nb_messages": Number of tasks
    - "nb_sessions": Number of sessions
    - "tags_count": Number of detected tags
    - "tags_distribution": Distribution of detected tags
    - "avg_success_rate": Average success rate
    - "avg_session_length": Average session length

    The "breakdown_by" field can be one of the following:
    - A metadata field
    - A time field: "day", "week", "month"
    - "tagger_name"
    - "task_position"
    - None
    - "session_length"
    """

    metric: Literal[
        "sum",
        "avg",
        "nb_messages",
        "nb_sessions",
        "tags_count",
        "avg_success_rate",
        "avg_session_length",
        "tags_distribution",
    ] = Field(
        "nb_messages",
        description="The metric to be analyzed.",
    )
    metric_metadata: str | None = Field(
        None,
        description="The metadata field to be analyzed.",
    )
    breakdown_by: (
        Literal[
            "day", "week", "month", "tagger_name", "task_position", "session_length"
        ]
        | str
        | None
    ) = Field(
        "day",
        description="The field to break down the metric by. Can be a metadata field, a time field, event_name, task_position, None, session_length",
    )
    filters: ProjectDataFilters | None = None
