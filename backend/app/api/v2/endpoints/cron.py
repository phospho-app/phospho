from fastapi import APIRouter, BackgroundTasks

from loguru import logger
from app.services.mongo.extractor import collect_langsmith_data
from app.security.authorization import get_quota
from app.core import config
from app.services.mongo.cron import fetch_projects_to_sync
from app.services.mongo.cron import fetch_and_decrypt_langsmith_credentials

router = APIRouter(tags=["cron"])


async def run_langsmith_sync_pipeline():
    logger.debug("Running Langsmith synchronisation pipeline")

    projects_ids = await fetch_projects_to_sync()

    for project_id in projects_ids:
        langsmith_credentials = await fetch_and_decrypt_langsmith_credentials(
            project_id
        )

        org_plan = await get_quota(project_id)
        current_usage = org_plan.get("current_usage", 0)
        max_usage = org_plan.get("max_usage", config.PLAN_HOBBY_MAX_NB_DETECTIONS)

        background_tasks = BackgroundTasks()

        background_tasks.add_task(
            collect_langsmith_data,
            project_id,
            org_plan["org_id"],
            langsmith_credentials,
            current_usage,
            max_usage,
        )

    return {"status": "ok", "message": "Pipeline ran successfully"}
