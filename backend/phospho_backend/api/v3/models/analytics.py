from phospho_backend.api.platform.models.metadata import (
    MetadataPivotResponse,
    MetadataPivotQuery,
)
from phospho_backend.api.platform.models import Users, QueryUserMetadataRequest
from phospho_backend.api.platform.models.explore import Sorting


class AnalyticsQuery(MetadataPivotQuery):
    project_id: str


class AnalyticsResponse(MetadataPivotResponse):
    pivot_table: list
