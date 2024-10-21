from app.api.platform.models.metadata import (
    MetadataPivotResponse,
    MetadataPivotQuery,
)
from app.api.platform.models import Users, QueryUserMetadataRequest
from app.api.platform.models.explore import Sorting


class AnalyticsQuery(MetadataPivotQuery):
    project_id: str


class AnalyticsResponse(MetadataPivotResponse):
    pass
