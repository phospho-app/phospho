from typing import Literal
from loguru import logger

from app.db.models import Job
from app.db.mongo import get_mongo_db


async def create_job(
    org_id: str,
    project_id: str,
    job_type: str,  #  Literal["evaluation", "event_detection"]
    parameters: dict,
    status: Literal["enabled", "deleted"] = "enabled",
    raise_error_if_exists: bool = False,
) -> Job:
    """
    Create a job in the database.
    """
    mongo_db = await get_mongo_db()

    # Validate the job
    job = Job(
        org_id=org_id,
        project_id=project_id,
        job_type=job_type,
        parameters=parameters,
        status=status,
    )

    result = await mongo_db["jobs"].insert_one(job.model_dump())

    logger.info(
        f"Job {job.id} created for project {project_id} with parameters {parameters}"
    )

    return job
