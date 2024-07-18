"""
To check if an organization has access to an argilla workspace, there is a metadata 'argilla_workspace_id' in the organization metadata.
"""

from fastapi import APIRouter, Depends, HTTPException
from propelauth_py.user import User
from app.services.mongo.integrations import (
    generate_dataset_from_project,
    get_power_bi_credentials,
    update_power_bi_status,
    export_project_to_dedicated_postgres,
)
from app.api.platform.models.integrations import DatasetCreationRequest
from app.services.mongo.integrations import dataset_name_is_valid
from app.services.mongo.projects import get_project_by_id
from app.core import config

from app.security.authentification import propelauth
from loguru import logger
from app.api.platform.models.integrations import PowerBICredentials

router = APIRouter(tags=["Integrations"])


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


@router.get("/powerbi/{org_id}", response_model=PowerBICredentials)
async def get_dedicated_db(org_id: str, user: User = Depends(propelauth.require_user)):
    org_member_info = propelauth.require_org_member(user, org_id)
    org = propelauth.fetch_org(org_member_info.org_id)

    # Get the org metadata
    org_metadata = org.get("metadata", {})

    if "power_bi" not in org_metadata or not org_id:
        raise HTTPException(
            status_code=400,
            detail="Your organization does not have access to a dedicated Power BI workspace. Contact us to get access to one.",
        )

    db_credentials = await get_power_bi_credentials(org_id=org_id)

    return db_credentials


@router.post("/powerbi/{project_id}")
async def start_project_extract(
    project_id: str, user: User = Depends(propelauth.require_user)
):
    project = await get_project_by_id(project_id)
    org_member_info = propelauth.require_org_member(user, project.org_id)

    org = propelauth.fetch_org(org_member_info.org_id)

    # Get the org metadata
    org_metadata = org.get("metadata", {})

    if "power_bi" not in org_metadata or not org_metadata["power_bi"]:
        raise HTTPException(
            status_code=400,
            detail="Your organization does not have access to a dedicated Power BI workspace. Contact us to get access to one.",
        )

    logger.debug(f"Starting the extract for project {project_id}")

    credentials = await get_power_bi_credentials(org_id=org_member_info.org_id)

    # The project has already been started or finished
    if (
        project_id in credentials.projects_started
        or project_id in credentials.projects_finished
    ):
        return {"status": "ok"}

    # Update the project status to "started"
    await update_power_bi_status(
        org_id=org_member_info.org_id, project_id=project_id, status="started"
    )

    # Debug in local environement
    if config.ENVIRONMENT == "test":
        debug = True
    else:
        debug = False

    # Start the extract
    try:
        await export_project_to_dedicated_postgres(
            project.project_name, project_id, credentials, debug=debug
        )
    except Exception as e:
        logger.error(f"Error while exporting the project to Power BI: {e}")
        await update_power_bi_status(
            org_id=org_member_info.org_id, project_id=project_id, status="failed"
        )
        raise HTTPException(
            status_code=400,
            detail="The extract could not be started. Please try again later.",
        )

    await update_power_bi_status(
        org_id=org_member_info.org_id, project_id=project_id, status="completed"
    )

    return {"status": "ok"}
