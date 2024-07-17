"""
To check if an organization has access to an argilla workspace, there is a metadata 'argilla_workspace_id' in the organization metadata.
"""

from fastapi import APIRouter, Depends, HTTPException
from propelauth_py.user import User
from app.services.mongo.datasets import (
    generate_dataset_from_project,
    get_workspace_datasets,
)
from app.api.platform.models.datasets import DatasetCreationRequest
from app.services.mongo.datasets import dataset_name_is_valid
from argilla import FeedbackDataset
from loguru import logger
from app.services.mongo.projects import get_project_by_id
from app.core import config

from app.security.authentification import propelauth

router = APIRouter(tags=["Datasets"])


@router.post("/datasets")
async def post_create_dataset(
    request: DatasetCreationRequest, user: User = Depends(propelauth.require_user)
):
    # TODO: Check if the user has access to the porject and the workspace

    project = await get_project_by_id(request.project_id)
    org_member_info = propelauth.require_org_member(user, project.org_id)

    org = propelauth.fetch_org(org_member_info.org_id)

    # Get the org metadata
    org_metadata = org.get("metadata", {})

    # Check if the organization has access to the workspace
    if "argilla_workspace_id" not in org_metadata:
        raise HTTPException(
            status_code=400,
            detail="Your organization does not have access to an Argilla workspace. Contact us to get access to one.",
        )

    workspace_id = org_metadata["argilla_workspace_id"]

    if workspace_id is request.workspace_id:
        raise HTTPException(status_code=400, detail="The workspace_id is not valid.")

    if request.limit > config.MAX_NUMBER_OF_DATASET_SAMPLES:
        raise HTTPException(
            status_code=400,
            detail=f"The limit must be less than {config.MAX_NUMBER_OF_DATASET_SAMPLES}.",
        )

    # Authorization checks
    is_name_valid = dataset_name_is_valid(request.dataset_name, request.workspace_id)

    if not is_name_valid:
        raise HTTPException(
            status_code=400, detail="The dataset name is not valid or already exists."
        )

    dataset = await generate_dataset_from_project(request)

    if dataset is None:
        raise HTTPException(
            status_code=400,
            detail="The dataset could not be generated using these filters.",
        )

    return {"status": "ok"}
