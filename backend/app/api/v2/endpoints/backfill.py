"""
API endpoint to backfill historical data
This can be used to backfill historical data, or to load a database into phospho
We do not use the regular log route, as we want to be able to:
- request a recompute or not
- already add some tags (evals, events,...) to the data
"""

from fastapi import APIRouter, Depends

from loguru import logger

from app.api.v2.models import BackfillBatchRequest
from app.security import authenticate_org_key, verify_propelauth_org_owns_project_id
from app.db.mongo import get_mongo_db


router = APIRouter(tags=["Backfill"])


@router.post(
    "/backfill/{project_id}",
    description="Log a batch of historical tasks. created_at (Unix timestamp in seconds) is required",
)
async def post_backfill(
    project_id: str,
    backfill_batch_request: BackfillBatchRequest,
    org: dict = Depends(authenticate_org_key),
):
    await verify_propelauth_org_owns_project_id(org, project_id)

    # TODO: backfill_batch_max_size

    mongo_db = await get_mongo_db()

    for task in backfill_batch_request.tasks:
        if task.project_id is None:
            # We set the project_id if it is not set
            task.project_id = project_id

        elif task.project_id != project_id:
            logger.warning(
                f"Task project_id {task.project_id} is different from the project_id {project_id}, skipping"
            )
            continue

        elif task.created_at is None:
            # For a backfill, we need to have a created_at
            logger.warning(f"Task {task.id} has no created_at, skipping")
            continue

        # The task is added to the db
        doc_creation = await mongo_db["tasks"].insert_one(task.model_dump())

        if not doc_creation:
            logger.error(f"Failed to insert the task {task.id} in database")

    return {"message": "Tasks logged"}
