import datetime

from fastapi import APIRouter, Header, Request
from fastapi_simple_rate_limiter import rate_limiter  # type: ignore

from phospho_backend.core import config
from phospho_backend.services.mongo.cron import (
    run_langfuse_sync_pipeline,
    run_langsmith_sync_pipeline,
    run_postgresql_sync_pipeline,
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
        # Only run the PostgreSQL sync pipeline once a day, at 10am
        if datetime.datetime.now().hour == 10:
            await run_postgresql_sync_pipeline()
        return {"status": "ok", "message": "Pipelines ran successfully"}
    except Exception as e:
        return {"status": "error", "message": f"Error running sync pipeline {e}"}
