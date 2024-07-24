from app.api.v1.models import (
    LogProcessRequestForMessages,
    LogProcessRequestForTasks,
    PipelineLangfuseRequest,
    PipelineLangsmithRequest,
    PipelineOpentelemetryRequest,
    PipelineResults,
    RunMainPipelineOnMessagesRequest,
    RunMainPipelineOnTaskRequest,
    RunRecipeOnTaskRequest,
)
from app.db.mongo import get_mongo_db
from app.security.authentication import authenticate_key
from app.services.connectors import (
    LangfuseConnector,
    LangsmithConnector,
    OpenTelemetryConnector,
)
from app.services.log import process_log_for_tasks, process_logs_for_messages
from app.services.pipelines import (
    messages_main_pipeline,
    recipe_pipeline,
    task_main_pipeline,
    task_scoring_pipeline,
)
from fastapi import APIRouter, BackgroundTasks, Depends
from loguru import logger

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
        save_task=request_body.save_results,
    )
    return pipeline_results


@router.post(
    "/pipelines/eval/task",
    description="Eval extractor pipeline",
    response_model=PipelineResults,
)
async def post_eval_pipeline_on_task(
    request_body: RunMainPipelineOnTaskRequest,
    is_request_authenticated: bool = Depends(authenticate_key),
) -> PipelineResults:
    logger.debug(f"task: {request_body.task}")
    # Do the session scoring -> success, failure
    mongo_db = await get_mongo_db()

    if request_body.save_results:
        task_in_db = await mongo_db["tasks"].find_one({"id": request_body.task.id})
        if task_in_db.get("flag") is None:
            flag = await task_scoring_pipeline(
                request_body.task, save_task=request_body.save_results
            )
        else:
            flag = task_in_db.get("flag")
    else:
        flag = await task_scoring_pipeline(
            request_body.task, save_task=request_body.save_results
        )

    pipeline_results = PipelineResults(
        events=[],
        flag=flag,
        language=None,
        sentiment=None,
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
async def post_log_tasks(
    request_body: LogProcessRequestForTasks,
    background_tasks: BackgroundTasks,
    is_request_authenticated: bool = Depends(authenticate_key),
):
    logger.info(
        f"Project {request_body.project_id} org {request_body.org_id}: processing {len(request_body.logs_to_process)} logs and saving {len(request_body.extra_logs_to_save)} extra logs."
    )
    background_tasks.add_task(
        process_log_for_tasks,
        project_id=request_body.project_id,
        org_id=request_body.org_id,
        logs_to_process=request_body.logs_to_process,
        extra_logs_to_save=request_body.extra_logs_to_save,
    )
    return {
        "status": "ok",
        "nb_job_results": len(request_body.logs_to_process),
    }


@router.post(
    "/pipelines/log/messages",
    description="Store a batch of log events in database",
)
async def post_log_messages(
    request_body: LogProcessRequestForMessages,
    background_tasks: BackgroundTasks,
    is_request_authenticated: bool = Depends(authenticate_key),
):
    logger.info(
        f"Project {request_body.project_id} org {request_body.org_id}: processing {len(request_body.logs_to_process)} logs and saving {len(request_body.extra_logs_to_save)} extra logs."
    )
    await process_logs_for_messages(
        project_id=request_body.project_id,
        org_id=request_body.org_id,
        logs_to_process=request_body.logs_to_process,
        extra_logs_to_save=request_body.extra_logs_to_save,
    )
    return {
        "status": "ok",
        "nb_job_results": len(request_body.logs_to_process),
    }


@router.post(
    "/pipelines/recipes",
    description="Run a recipe on tasks",
)
async def post_run_job_on_task(
    request: RunRecipeOnTaskRequest,
    background_tasks: BackgroundTasks,
    is_request_authenticated: bool = Depends(authenticate_key),
):
    # If there are no tasks to process, return
    if len(request.tasks) == 0:
        logger.debug("No tasks to process.")
        return {"status": "no tasks to process", "nb_job_results": 0}
    # Run the valid recipes
    logger.info(
        f"Running job {request.recipe.recipe_type} on {len(request.tasks)} tasks."
    )
    background_tasks.add_task(
        recipe_pipeline,
        tasks=request.tasks,
        recipe=request.recipe,
    )
    return {"status": "ok", "nb_job_results": len(request.tasks)}


@router.post(
    "/pipelines/opentelemetry",
    response_model=dict,
    description="Store data from OpenTelemetry in database",
)
async def store_opentelemetry_data(
    request: PipelineOpentelemetryRequest,
) -> dict:
    """Store the opentelemetry data in the opentelemetry database"""

    opentelemetry_connector = OpenTelemetryConnector(
        project_id=request.project_id,
        data=request.open_telemetry_data,
    )
    await opentelemetry_connector.process(
        org_id=request.org_id,
        current_usage=request.current_usage,
        max_usage=request.max_usage,
    )

    return {"status": "ok"}


@router.post(
    "/pipelines/langsmith",
    description="Run the Langsmith pipeline",
)
async def extract_langsmith_data(
    request: PipelineLangsmithRequest,
):
    logger.debug(f"Received Langsmith connection data for org id: {request.org_id}")

    langsmith_connector = LangsmithConnector(
        project_id=request.project_id,
        langsmith_api_key=request.langsmith_api_key,
        langsmith_project_name=request.langsmith_project_name,
    )
    return await langsmith_connector.sync(
        org_id=request.org_id,
        current_usage=request.current_usage,
        max_usage=request.max_usage,
    )


@router.post(
    "/pipelines/langfuse",
    description="Run the langfuse pipeline on a task",
)
async def extract_langfuse_data(
    request: PipelineLangfuseRequest,
):
    logger.debug(f"Received LangFuse connection data for org id: {request.org_id}")

    langfuse_connector = LangfuseConnector(
        project_id=request.project_id,
        langfuse_secret_key=request.langfuse_secret_key,
        langfuse_public_key=request.langfuse_public_key,
    )

    return await langfuse_connector.sync(
        org_id=request.org_id,
        current_usage=request.current_usage,
        max_usage=request.max_usage,
    )
