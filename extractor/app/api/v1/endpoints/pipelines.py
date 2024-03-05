from fastapi import APIRouter, Depends, BackgroundTasks
from loguru import logger

# Security
from app.security.authentication import authenticate_key

# Services
from app.services.pipelines import main_pipeline
from app.services.log import process_log

# Models
from app.api.v1.models import MainPipelineRequest, LogProcessRequest

router = APIRouter()


@router.post(
    "/pipelines/main",
    description="Main extractor pipeline",
)
async def post_main_pipeline(
    request_body: MainPipelineRequest,
    background_tasks: BackgroundTasks,
    is_request_authenticated: bool = Depends(authenticate_key),
):
    logger.debug(f"task: {request_body.task}")
    if is_request_authenticated:
        background_tasks.add_task(main_pipeline, request_body.task)
    return {"status": "ok"}


@router.post(
    "/pipelines/log",
    description="Store a batch of log events in database",
)
async def post_log(
    request_body: LogProcessRequest,
    background_tasks: BackgroundTasks,
    is_request_authenticated: bool = Depends(authenticate_key),
):
    if is_request_authenticated:
        background_tasks.add_task(
            process_log,
            project_id=request_body.project_id,
            org_id=request_body.org_id,
            logs_to_process=request_body.logs_to_process,
        )
    return {"status": "ok"}
