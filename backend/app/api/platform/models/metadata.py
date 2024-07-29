from typing import Optional
from pydantic import BaseModel, Field
from phospho.models import ProjectDataFilters


class MetadataValueResponse(BaseModel):
    value: Optional[float]


class MetadataPivotResponse(BaseModel):
    pivot_table: list


class MetadataPivotQuery(BaseModel):
    metric: str
    metric_metadata: str | None
    number_metadata_fields: list[str] = Field(default_factory=list)
    category_metadata_fields: list[str] = Field(default_factory=list)
    breakdown_by: str | None
    filters: ProjectDataFilters | None = None
