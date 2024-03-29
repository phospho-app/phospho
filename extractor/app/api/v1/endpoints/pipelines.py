from fastapi import APIRouter, Depends, BackgroundTasks
from loguru import logger

# Security
from app.security.authentication import authenticate_key

# Services
from app.services.pipelines import main_pipeline
from app.services.log import process_log

# Models
from app.api.v1.models import MainPipelineRequest, LogProcessRequest, PipelineResults

router = APIRouter()


@router.post(
    "/pipelines/main",
    description="Main extractor pipeline",
    response_model=PipelineResults,
)
async def post_main_pipeline(
    request_body: MainPipelineRequest,
    is_request_authenticated: bool = Depends(authenticate_key),
) -> PipelineResults:
    logger.debug(f"task: {request_body.task}")
    pipeline_results = await main_pipeline(request_body.task, save_task=False)
    return pipeline_results


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
        logger.info(
            f"Project {request_body.project_id} org {request_body.org_id}: processing {len(request_body.logs_to_process)} logs and saving {len(request_body.extra_logs_to_save)} extra logs."
        )
        background_tasks.add_task(
            process_log,
            project_id=request_body.project_id,
            org_id=request_body.org_id,
            logs_to_process=request_body.logs_to_process,
            extra_logs_to_save=request_body.extra_logs_to_save,
        )
    return {"status": "ok"}
