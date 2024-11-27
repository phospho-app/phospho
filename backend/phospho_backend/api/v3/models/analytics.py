from phospho_backend.api.platform.models import QueryUserMetadataRequest, Users
from phospho_backend.api.platform.models.explore import Sorting
from phospho_backend.api.platform.models.metadata import (
    MetadataPivotQuery,
    MetadataPivotResponse,
)


class AnalyticsQuery(MetadataPivotQuery):
    project_id: str


class AnalyticsResponse(MetadataPivotResponse):
    pivot_table: list
