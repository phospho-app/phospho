"""
To check if an organization has access to an argilla workspace, there is a metadata 'argilla_workspace_id' in the organization metadata.
"""

from fastapi import APIRouter, Depends, HTTPException
from propelauth_py.user import User
from app.services.mongo.datasets import generate_dataset_from_project
from app.api.platform.models.datasets import DatasetCreationRequest
from app.services.mongo.datasets import dataset_name_is_valid

from app.security.authentification import propelauth

router = APIRouter(tags=["Datasets"])


@router.get("/datasets")
def get_datasets(user: User = Depends(propelauth.require_user)):
    raise NotImplementedError("Not implemented yet.")


@router.post("/datasets")
async def post_create_dataset(
    request: DatasetCreationRequest,
):  # user: User = Depends(propelauth.require_user)):
    # TODO: Check if the user has access to the porject and the workspace

    # Authorization checks
    is_name_valid = dataset_name_is_valid(request.dataset_name, request.workspace_id)

    if not is_name_valid:
        raise HTTPException(
            status_code=400, detail="The dataset name is not valid or already exists."
        )

    dataset = await generate_dataset_from_project(request)
    return {"status": "TODO"}
