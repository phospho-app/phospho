from asyncio.log import logger

from fastapi import APIRouter, Depends
from propelauth_fastapi import User  # type: ignore

from phospho_backend.api.platform.models import RenameClusteringRequest
from phospho_backend.security.authentification import (
    propelauth,
    verify_if_propelauth_user_can_access_project,
)
from phospho_backend.services.mongo.clustering import rename_clustering

router = APIRouter(tags=["clustering"])


@router.post(
    "/clustering/{project_id}/rename",
    description="Rename a clustering",
)
async def post_rename_clustering(
    project_id: str,
    request: RenameClusteringRequest,
    user: User = Depends(propelauth.require_user),
):
    """
    Rename a clustering.
    """

    logger.debug(f"Renaming clustering {request.clustering_id} to {request.new_name}")
    await verify_if_propelauth_user_can_access_project(user, project_id)
    await rename_clustering(
        project_id=project_id,
        clustering_id=request.clustering_id,
        new_name=request.new_name,
    )
