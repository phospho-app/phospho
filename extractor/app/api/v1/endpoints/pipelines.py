from fastapi import APIRouter, Depends, BackgroundTasks
from loguru import logger

# Security
from app.security.authentication import authenticate_key

# Services
from app.services.pipelines import main_pipeline

# Models
from app.api.v1.models.pipelines import MainPipelineRequest

router = APIRouter()


# Main pipeline
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
