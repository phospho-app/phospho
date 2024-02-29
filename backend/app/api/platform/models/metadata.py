from typing import Any
from pydantic import BaseModel, Field


class MetadataValueResponse(BaseModel):
    value: float


class MetadataPivotResponse(BaseModel):
    pivot_table: list


class MetadataPivotQuery(BaseModel):
    metric: str
    metric_metadata: str | None
    number_metadata_fields: list[str] = Field(default_factory=list)
    category_metadata_fields: list[str] = Field(default_factory=list)
    breakdown_by: str | None
