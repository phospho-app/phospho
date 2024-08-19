from pydantic import BaseModel
from app.api.platform.models.metadata import (
    MetadataValueResponse,
    MetadataPivotResponse,
    MetadataPivotQuery,
)


class AnalyticsQuery(MetadataPivotQuery):
    project_id: str


class AnalyticsResponse(MetadataPivotResponse):
    pass
