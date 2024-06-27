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
from app.services.mongo.fine_tuning import start_fine_tuning_job, fetch_fine_tuning_job


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
        if org["org"]["metadata"].get("is_in_alpha", False):
            authorize_request = True

    if not authorize_request:
        logger.warning("Not authorized user tried to create a fine-tuning job.")
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

    # Start the fine-tuning job, pass it the fine_tuning_job object
    background_tasks.add_task(start_fine_tuning_job, fine_tuning_job)

    return fine_tuning_job


@router.get(
    "/fine_tuning/jobs/{job_id}",
    description="Get the status of a fine-tuning job.",
)
async def get_fine_tuning_job(
    job_id: str,
    org: dict = Depends(authenticate_org_key),
) -> FineTuningJob:
    fine_tuning_job = await fetch_fine_tuning_job(job_id)

    # Check the org owns the job
    if fine_tuning_job.org_id != org["org"].get("org_id"):
        raise HTTPException(
            status_code=403, detail="You are not authorized to view this job."
        )

    return fine_tuning_job
