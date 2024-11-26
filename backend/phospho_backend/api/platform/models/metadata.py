from typing import Literal

from phospho.models import ProjectDataFilters
from pydantic import BaseModel, Field


class MetadataValueResponse(BaseModel):
    value: float | None


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
    Query to pivot metadata fields.
    """

    metric: Literal[
        "sum",
        "avg",
        "count_unique",
        "nb_messages",
        "nb_sessions",
        "tags_count",
        "avg_scorer_value",
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
            "day",
            "week",
            "month",
            "tagger_name",
            "scorer_value",
            "classifier_value",
            "task_position",
            "session_length",
        ]
        | str
        | None
    ) = Field(
        "day",
        description="The field to break down the metric by. "
        + "If the metric is a free string, it will be interpreted as a metadata field.",
    )
    breakdown_by_event_id: str | None = Field(
        None,
        description="When using the scorer_value or classifier_value breakdown_by, this is the `EventDefinition.id` of the scorer or classifier. "
        + "Check the id in the Event page URL.",
    )
    scorer_id: str | None = Field(
        None,
        description="When using the avg_scorer_value metric, this is the `EventDefinition.id` of the scorer. "
        + "Check the id of the scorer in the Event page URL.",
    )
    filters: ProjectDataFilters | None = None
