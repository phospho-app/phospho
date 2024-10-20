"""
Endpoint for analytics queries
"""

import datetime
from fastapi import APIRouter, Depends
from app.security import (
    authenticate_org_key,
    verify_propelauth_org_owns_project_id,
)
from app.services.mongo.dataviz import breakdown_by_sum_of_metadata_field

from phospho.models import ProjectDataFilters
from app.api.v3.models.analytics import (
    AnalyticsQuery,
    AnalyticsResponse,
    Users,
    QueryUserMetadataRequest,
    Sorting,
)
from app.utils import cast_datetime_or_timestamp_to_timestamp
from app.services.mongo.users import fetch_users_metadata

router = APIRouter(tags=["Export"])


@router.post(
    "/export/analytics",
    description="Create a pivot table for metadata in a project.",
    response_model=AnalyticsResponse,
)
async def post_metadata_pivot(
    pivot_query: AnalyticsQuery,
    org: dict = Depends(authenticate_org_key),
) -> AnalyticsResponse:
    """
    Create a pivot table for metadata in a project.
    """
    await verify_propelauth_org_owns_project_id(org, pivot_query.project_id)

    if pivot_query.filters is None:
        pivot_query.filters = ProjectDataFilters()
    # Convert to UNIX timestamp in seconds
    if isinstance(pivot_query.filters.created_at_start, datetime.datetime):
        pivot_query.filters.created_at_start = int(
            pivot_query.filters.created_at_start.timestamp()
        )
    if isinstance(pivot_query.filters.created_at_end, datetime.datetime):
        pivot_query.filters.created_at_end = int(
            pivot_query.filters.created_at_end.timestamp()
        )

    pivot_table = await breakdown_by_sum_of_metadata_field(
        project_id=pivot_query.project_id,
        metric=pivot_query.metric,
        metadata_field=pivot_query.metric_metadata,
        breakdown_by=pivot_query.breakdown_by,
        filters=pivot_query.filters,
    )

    return AnalyticsResponse(pivot_table=pivot_table)


@router.post(
    "/export/projects/{project_id}/users",
    response_model=Users,
    description="Get all the metadata about the end-users of a project",
)
async def get_users(
    project_id: str,
    query: QueryUserMetadataRequest,
    org: dict = Depends(authenticate_org_key),
) -> Users:
    """
    Get metadata about the end-users of a project
    """
    await verify_propelauth_org_owns_project_id(org, project_id)

    filters = query.filters
    if isinstance(filters.created_at_start, datetime.datetime):
        filters.created_at_start = cast_datetime_or_timestamp_to_timestamp(
            filters.created_at_start
        )
    if isinstance(filters.created_at_end, datetime.datetime):
        filters.created_at_end = cast_datetime_or_timestamp_to_timestamp(
            filters.created_at_end
        )

    if query.sorting is None:
        query.sorting = [
            Sorting(id="last_message_ts", desc=True),
            Sorting(id="user_id", desc=True),
        ]
    else:
        # Always resort by user_id to ensure the same order
        # when multiple users have the same last_timestamp_ts or values
        query.sorting.append(Sorting(id="user_id", desc=True))

    users = await fetch_users_metadata(
        project_id=project_id,
        filters=filters,
        sorting=query.sorting,
        pagination=query.pagination,
        user_id_search=query.user_id_search,
    )
    return Users(users=users)
