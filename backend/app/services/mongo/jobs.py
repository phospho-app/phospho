from typing import Literal
from loguru import logger
import time

from app.db.models import Job, Task
from app.db.mongo import get_mongo_db
from app.services.mongo.extractor import run_job_on_tasks


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


async def backcompute_job(
    project_id: str,
    job_id: str,
    limit: int = 10000,
    timestamp_limit: int = 0,  # Unix timestamp limit, default to the implementation date of the feature: 1713885864
    wait_time: float = 10 / 10000,  # In seconds. We have a rate limit of 10k RPM
) -> Job:
    """
    Run predictions for a job on all the tasks of a project that have not been processed yet.
    """
    mongo_db = await get_mongo_db()

    # Get all the tasks of the project
    tasks = (
        await mongo_db["tasks"]
        .find({"project_id": project_id, "created_at": {"$gt": timestamp_limit}})
        .sort("timestamp", -1)
        .to_list(limit)
    )

    # Make them Task objects
    tasks = [Task(**task) for task in tasks]

    # Get the job using it's id
    job = await mongo_db["jobs"].find_one({"id": job_id})
    # Make it a Job object
    job = Job(**job)

    # Display a warning if the number of tasks is greater than the limit
    if len(tasks) >= limit:
        logger.error(
            f"Number of tasks {len(tasks)} is greater than the limit {limit}, only the first {limit} tasks will be processed"
        )

    # For each task, check if a prediction has a job_id and a task_id matching the task
    for task in tasks:
        # Check if the task has been processed
        if not await mongo_db["predictions"].find_one(
            {"task_id": task.id, "job_id": job.id}
        ):
            # If not, run the prediction
            logger.debug(f"Running prediction fo job {job_id} for task {task.id}")
            await run_job_on_tasks(task, job)
            time.sleep(wait_time)

        else:
            logger.debug(
                f"Prediction for job {job_id} and task {task.id} already exists"
            )
