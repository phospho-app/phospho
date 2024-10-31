"""
To check if an organization has access to an argilla workspace, there is a metadata 'argilla_workspace_id' in the organization metadata.
"""

from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from propelauth_py.user import User

from app.api.platform.models.integrations import (
    DatasetCreationRequest,
    DatasetPullRequest,
)
from app.core import config
from app.security.authentification import (
    propelauth,
    verify_if_propelauth_user_can_access_project,
)
from app.services.integrations import (
    dataset_name_is_valid,
    dataset_name_exists,
    get_datasets_name,
    generate_dataset_from_project,
    pull_dataset_from_argilla,
    PostgresqlCredentials,
    PostgresqlIntegration,
)
from app.services.mongo.projects import get_project_by_id

router = APIRouter(tags=["Integrations"])


@router.post("/argilla/datasets/create")
async def post_create_dataset(
    request: DatasetCreationRequest, user: User = Depends(propelauth.require_user)
):
    await verify_if_propelauth_user_can_access_project(user, request.project_id)
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
    if request.workspace_id != workspace_id:
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
    await generate_dataset_from_project(request)
    return {"status": "ok"}


@router.get("/postgresql/creds/{org_id}", response_model=PostgresqlCredentials)
async def get_postgresql_creds(
    org_id: str, user: User = Depends(propelauth.require_user)
):
    org_member_info = propelauth.require_org_member(user, org_id)
    org = propelauth.fetch_org(org_member_info.org_id)
    org_metadata = org.get("metadata", {})
    org_name = org.get("name", None)
    postgres_integration = PostgresqlIntegration(
        org_id=org_id, org_metadata=org_metadata, org_name=org_name
    )
    await postgres_integration.load_config()
    return postgres_integration.credentials


@router.post("/postgresql/push/{project_id}")
async def post_postgresql_push(
    project_id: str, user: User = Depends(propelauth.require_user)
):
    await verify_if_propelauth_user_can_access_project(user, project_id)
    project = await get_project_by_id(project_id)
    org_member_info = propelauth.require_org_member(user, project.org_id)
    org = propelauth.fetch_org(org_member_info.org_id)
    org_metadata = org.get("metadata", {})
    org_name = org.get("name", None)
    postgres_integration = PostgresqlIntegration(
        org_id=org_member_info.org_id,
        org_name=org_name,
        org_metadata=org_metadata,
        project_id=project_id,
        project_name=project.project_name,
    )
    status = await postgres_integration.push()
    return {"status": status}


@router.post("/argilla/datasets/pull")
async def post_pull_dataset(
    request: DatasetPullRequest, user: User = Depends(propelauth.require_user)
):
    await verify_if_propelauth_user_can_access_project(user, request.project_id)
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
    if request.workspace_id != workspace_id:
        raise HTTPException(status_code=400, detail="The workspace_id is not valid.")

    if request.dataset_name is None:
        # We have to implement this manually because DatasetPullRequest is also
        # used for fetching the dataset names, where dataset_name is not required.
        raise HTTPException(
            status_code=400, detail="The dataset name must be provided."
        )

    # Authorization checks
    is_name_valid = dataset_name_exists(
        request.dataset_name, request.workspace_id, request.project_id
    )
    if not is_name_valid:
        raise HTTPException(
            status_code=400, detail="The dataset name does not exist for this project."
        )
    await pull_dataset_from_argilla(request)

    return {"status": "ok"}


@router.post("/argilla/datasets/names")
async def post_fetch_dataset_names(
    request: DatasetPullRequest, user: User = Depends(propelauth.require_user)
):
    logger.debug(f"Request: {request.model_dump()}")
    logger.debug(f"project_id: {request.project_id}")
    logger.debug(f"workspace_id: {request.workspace_id}")
    await verify_if_propelauth_user_can_access_project(user, request.project_id)
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
    if request.workspace_id != workspace_id:
        raise HTTPException(status_code=400, detail="The workspace_id is not valid.")

    datasets_name = get_datasets_name(request.workspace_id, request.project_id)

    logger.debug(f"Datasets name: {datasets_name}")

    return datasets_name
