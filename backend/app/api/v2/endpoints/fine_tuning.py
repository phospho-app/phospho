"""
For now, it's pretty much a fine-tuning endpoint.
Other optimization methods might be added in the future.
Might lead to the creation of a new `optimize` endpoint.
"""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from loguru import logger

from app.security import (
    authenticate_org_key,
)
from app.db.models import FineTuningJob
from app.api.v2.models.fine_tuning import FineTuningJobCreationRequest


router = APIRouter(tags=["Fine-tuning"])


@router.post(
    "/fine_tuning/jobs",
    description="Creates a fine-tuning job which begins the process of creating a new model from a given dataset.",
)
async def create_fine_tuning_job(
    fine_tuning_job_creation_request: FineTuningJobCreationRequest,
    background_tasks: BackgroundTasks,
    org: dict = Depends(authenticate_org_key),
):
    authorize_request = False

    # Check that the org is a pro user to use this feature
    # Might add more checks in the future
    if org["org"].get("metadata", None) is not None:
        logger.debug(f"Org metadata: {org['org']['metadata']}")
        if org["org"]["metadata"].get("plan") == "pro":
            authorize_request = True

    if not authorize_request:
        raise HTTPException(
            status_code=403, detail="You need to be a pro user to use this feature."
        )

    fine_tuning_job = FineTuningJob(
        org_id=org["org"].get("org_id"),
        file_id=fine_tuning_job_creation_request.file_id,
        parameters=fine_tuning_job_creation_request.parameters,
        model=fine_tuning_job_creation_request.model,
        status="started",
    )

    # Store the fine-tuning job in the database

    # Start the fine-tuning job

    return fine_tuning_job
