from fastapi import APIRouter, Header, Request
from fastapi_simple_rate_limiter import rate_limiter

from loguru import logger
from app.services.mongo.extractor import collect_langsmith_data, collect_langfuse_data
from app.security.authorization import get_quota
from app.core import config
from app.services.mongo.cron import fetch_projects_to_sync
from app.services.mongo.cron import (
    fetch_and_decrypt_langsmith_credentials,
    fetch_and_decrypt_langfuse_credentials,
)
from typing import Dict

router = APIRouter(tags=["cron"])


@router.post(
    "/cron/sync_pipeline",
    description="Run the synchronisation pipeline for Langsmith and Langfuse",
    response_model=Dict,
)
@rate_limiter(limit=2, seconds=60)
async def run_sync_pipeline(
    request: Request,
    key: str | None = Header(default=None),
):
    if key != config.CRON_SECRET_KEY:
        return {"status": "error", "message": "Invalid secret key"}
    try:
        await run_langsmith_sync_pipeline()
        await run_langfuse_sync_pipeline()
        return {"status": "ok", "message": "Pipeline ran successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Error running sync pipeline {e}"}


async def run_langsmith_sync_pipeline():
    logger.debug("Running Langsmith synchronisation pipeline")

    projects_ids = await fetch_projects_to_sync(type="langsmith")

    for project_id in projects_ids:
        langsmith_credentials = await fetch_and_decrypt_langsmith_credentials(
            project_id
        )

        org_plan = await get_quota(project_id)
        current_usage = org_plan.get("current_usage", 0)
        max_usage = org_plan.get("max_usage", config.PLAN_HOBBY_MAX_NB_DETECTIONS)

        await collect_langsmith_data(
            project_id=project_id,
            org_id=org_plan["org_id"],
            langsmith_credentials=langsmith_credentials,
            current_usage=current_usage,
            max_usage=max_usage,
        )

    return {"status": "ok", "message": "Pipeline ran successfully"}


async def run_langfuse_sync_pipeline():
    logger.debug("Running Langfuse synchronisation pipeline")

    projects_ids = await fetch_projects_to_sync(type="langfuse")

    for project_id in projects_ids:
        langfuse_credentials = await fetch_and_decrypt_langfuse_credentials(project_id)

        org_plan = await get_quota(project_id)
        current_usage = org_plan.get("current_usage", 0)
        max_usage = org_plan.get("max_usage", config.PLAN_HOBBY_MAX_NB_DETECTIONS)

        await collect_langfuse_data(
            project_id=project_id,
            org_id=org_plan["org_id"],
            langfuse_credentials=langfuse_credentials,
            current_usage=current_usage,
            max_usage=max_usage,
        )

    return {"status": "ok", "message": "Pipeline ran successfully"}
