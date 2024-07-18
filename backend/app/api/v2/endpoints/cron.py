from fastapi import APIRouter, Header, Request
from fastapi_simple_rate_limiter import rate_limiter

from app.core import config
from app.services.mongo.cron import (
    run_langfuse_sync_pipeline,
    run_langsmith_sync_pipeline,
)

router = APIRouter(tags=["cron"])


@router.post(
    "/cron/sync_pipeline",
    description="Run the synchronisation pipeline for Langsmith and Langfuse",
    response_model=dict,
)
@rate_limiter(limit=2, seconds=60)
async def run_sync_pipeline(
    request: Request,
    key: str | None = Header(default=None),
) -> dict:
    if key != config.CRON_SECRET_KEY:
        return {"status": "error", "message": "Invalid secret key"}
    try:
        await run_langsmith_sync_pipeline()
        await run_langfuse_sync_pipeline()
        return {"status": "ok", "message": "Pipelines ran successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Error running sync pipeline {e}"}
