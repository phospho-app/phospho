import datetime

from fastapi import APIRouter, Depends
from phospho.models import ProjectDataFilters
from propelauth_fastapi import User  # type: ignore

# Models
from phospho_backend.api.platform.models import (
    MetadataPivotQuery,
    MetadataPivotResponse,
)
from phospho_backend.security import verify_if_propelauth_user_can_access_project
from phospho_backend.security.authentification import propelauth

# Service
from phospho_backend.services.mongo.dataviz import (
    breakdown_by_sum_of_metadata_field,
    collect_unique_metadata_field_values,
    collect_unique_metadata_fields,
)

router = APIRouter(tags=["Metadata"])


@router.post(
    "/metadata/{project_id}/fields",
    description="Get the list of all unique metadata fields in a project.",
    response_model=dict[str, list[str]],
)
async def get_metadata_fields(
    project_id: str,
    user: User = Depends(propelauth.require_user),
) -> dict[str, list[str]]:
    """
    Get the list of all unique metadata fields names in a project.
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)
    unique_number_metadata_fields = await collect_unique_metadata_fields(
        project_id=project_id, type="number"
    )
    unique_string_metadata_fields = await collect_unique_metadata_fields(
        project_id=project_id, type="string"
    )
    return {
        "number": unique_number_metadata_fields,
        "string": unique_string_metadata_fields,
    }


@router.post(
    "/metadata/{project_id}/fields/values",
    description="Get a list of all unique metadata fields values in a project, with their associated unique values.",
    response_model=dict[str, dict[str, list[str]]],
)
async def get_metadata_fields_values(
    project_id: str,
    user: User = Depends(propelauth.require_user),
) -> dict[str, dict[str, list[str]]]:
    """
    Get the list of all unique metadata fields values in a project.
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)
    metadata_fields_to_unique_values = await collect_unique_metadata_field_values(
        project_id=project_id, type="string"
    )
    return {
        "number": {},  # TODO: implement group of values/ranges?
        "string": metadata_fields_to_unique_values,
    }


@router.post(
    "/metadata/{project_id}/pivot",
    description="Create a pivot table for metadata in a project.",
    response_model=MetadataPivotResponse,
)
async def post_metadata_pivot(
    project_id: str,
    pivot_query: MetadataPivotQuery,
    user: User = Depends(propelauth.require_user),
) -> MetadataPivotResponse:
    """
    Create a pivot table for metadata in a project.
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)
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
        project_id=project_id,
        pivot_query=pivot_query,
    )

    return MetadataPivotResponse(pivot_table=pivot_table)
