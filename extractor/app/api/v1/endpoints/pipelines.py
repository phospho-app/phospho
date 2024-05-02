from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from loguru import logger

# Security
from app.security.authentication import authenticate_key

# Services
from app.services.pipelines import (
    task_main_pipeline,
    messages_main_pipeline,
    recipe_pipeline,
)
from app.services.log import process_log

# Models
from app.api.v1.models import (
    RunMainPipelineOnTaskRequest,
    LogProcessRequest,
    PipelineResults,
    RunMainPipelineOnMessagesRequest,
    RunRecipeOnTaskRequest,
)

router = APIRouter()


@router.post(
    "/pipelines/main/task",
    description="Main extractor pipeline",
    response_model=PipelineResults,
)
async def post_main_pipeline_on_task(
    request_body: RunMainPipelineOnTaskRequest,
    is_request_authenticated: bool = Depends(authenticate_key),
) -> PipelineResults:
    logger.debug(f"task: {request_body.task}")
    pipeline_results = await task_main_pipeline(
        task=request_body.task,
        save_task=False,
    )
    return pipeline_results


@router.post(
    "/pipelines/main/messages",
    description="Main extractor pipeline on messages",
    response_model=PipelineResults,
)
async def post_main_pipeline_on_messages(
    request_body: RunMainPipelineOnMessagesRequest,
    is_request_authenticated: bool = Depends(authenticate_key),
) -> PipelineResults:
    pipeline_results = await messages_main_pipeline(
        project_id=request_body.project_id,
        messages=request_body.messages,
    )
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
    return {"status": "ok", "nb_job_results": len(request_body.logs_to_process)}


@router.post(
    "/pipelines/recipes",
    description="Run a recipe on a task",
)
async def post_run_job_on_task(
    background_tasks: BackgroundTasks,
    request: RunRecipeOnTaskRequest,
    is_request_authenticated: bool = Depends(authenticate_key),
):
    # If there is no tasks to process, return
    if len(request.tasks) == 0:
        logger.debug("No tasks to process.")
        return {"status": "no tasks to process"}

    if request.recipe.recipe_type == "event_detection":
        logger.info(
            f"Running job {request.recipe.recipe_type} on {len(request.tasks)} tasks."
        )
        background_tasks.add_task(
            recipe_pipeline,
            tasks=request.tasks,
            recipe=request.recipe,
        )
        return {"status": "ok"}

    else:
        raise HTTPException(
            status_code=400,
            detail="Invalid job type. Only 'event_detection' is supported.",
        )
