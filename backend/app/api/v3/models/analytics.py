from app.api.platform.models.metadata import (
    MetadataPivotResponse,
    MetadataPivotQuery,
)


class AnalyticsQuery(MetadataPivotQuery):
    project_id: str


class AnalyticsResponse(MetadataPivotResponse):
    pass
