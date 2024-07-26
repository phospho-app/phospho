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
from app.services.pipelines import MainPipeline
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
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
    if request_body.task.org_id is None:
        raise HTTPException(
            status_code=400,
            detail="Task.org_id is missing.",
        )
    main_pipeline = MainPipeline(
        project_id=request_body.task.project_id,
        org_id=request_body.task.org_id,
    )
    pipeline_results = await main_pipeline.task_main_pipeline(task=request_body.task)
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
    if request_body.task.org_id is None:
        raise HTTPException(
            status_code=400,
            detail="Task.org_id is missing.",
        )
    main_pipeline = MainPipeline(
        project_id=request_body.task.project_id,
        org_id=request_body.task.org_id,
    )
    await main_pipeline.set_input(task=request_body.task)
    flag = await main_pipeline.run_evaluation()
    return PipelineResults(
        flag=flag,
    )


@router.post(
    "/pipelines/main/messages",
    description="Detect events, eval, and everything else on continuous messages of a single session.",
    response_model=PipelineResults,
)
async def post_main_pipeline_on_messages(
    request_body: RunMainPipelineOnMessagesRequest,
    is_request_authenticated: bool = Depends(authenticate_key),
) -> PipelineResults:
    main_pipeline = MainPipeline(
        project_id=request_body.project_id,
        org_id=request_body.org_id,
    )
    await main_pipeline.set_input(messages=request_body.messages)
    pipeline_results = await main_pipeline.run()
    return pipeline_results


@router.post(
    "/pipelines/log",
    description="Store and process a batch of log events in the database",
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
    description="! Not implemented",
)
async def post_log_messages(
    request_body: LogProcessRequestForMessages,
    background_tasks: BackgroundTasks,
    is_request_authenticated: bool = Depends(authenticate_key),
):
    """
    Not implemented
    """
    logger.info(
        f"Project {request_body.project_id} org {request_body.org_id}: processing {len(request_body.logs_to_process)} logs and saving {len(request_body.extra_logs_to_save)} extra logs."
    )
    background_tasks.add_task(
        process_logs_for_messages,
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
    if len(request.tasks) == 0:
        logger.debug("No tasks to process.")
        return {"status": "no tasks to process", "nb_job_results": 0}
    logger.info(
        f"Running job {request.recipe.recipe_type} on {len(request.tasks)} tasks."
    )
    if request.recipe.org_id is None:
        raise HTTPException(
            status_code=400,
            detail="Recipe.org_id is missing.",
        )
    main_pipeline = MainPipeline(
        project_id=request.recipe.project_id,
        org_id=request.recipe.org_id,
    )
    background_tasks.add_task(
        main_pipeline.recipe_pipeline,
        tasks=request.tasks,
        recipe=request.recipe,
    )
    return {"status": "ok", "nb_job_results": len(request.tasks)}


@router.post(
    "/pipelines/opentelemetry",
    response_model=dict,
    description="Store data from OpenTelemetry in a dedicated database",
)
async def store_opentelemetry_data(
    request: PipelineOpentelemetryRequest,
) -> dict:
    """
    Store the opentelemetry data in the opentelemetry database
    Doesn't process logs
    """

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
    description="Pull data from Langsmith and process it",
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
    description="Pull data from LangFuse and process it",
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
