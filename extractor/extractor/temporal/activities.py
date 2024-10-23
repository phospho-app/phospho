import time
from temporalio import activity

import stripe
from extractor.core import config
from extractor.services.pipelines import MainPipeline
from extractor.services.connectors import (
    LangsmithConnector,
    LangfuseConnector,
    OpenTelemetryConnector,
)
from extractor.services.log.tasks import process_tasks_id
from extractor.models.log import TaskProcessRequest
from extractor.models import (
    PipelineLangfuseRequest,
    PipelineLangsmithRequest,
    PipelineOpentelemetryRequest,
    PipelineResults,
    RunMainPipelineOnMessagesRequest,
    RunMainPipelineOnTaskRequest,
    RunRecipeOnTaskRequest,
    BillOnStripeRequest,
)
from extractor.services.projects import get_project_by_id
from extractor.models.log import LogProcessRequestForTasks
from loguru import logger
from extractor.services.log.tasks import process_logs_for_tasks


@activity.defn(name="bill_on_stripe")
async def bill_on_stripe(
    request: BillOnStripeRequest,
) -> None:
    """
    Bill an organization on Stripe based on the consumption
    """
    if request.nb_job_results == 0:
        logger.debug(f"No job results to bill for organization {request.org_id}")
        return

    if request.max_usage and request.current_usage < request.max_usage:
        logger.debug(
            f"Organization {request.org_id} has not reached max usage {request.max_usage}"
        )
        return

    logger.info(
        f"Billing organization {request.org_id} for {request.nb_job_results} jobs, project_id {request.project_id}"
    )
    usage_per_log: int = 0
    project = await get_project_by_id(request.project_id)
    if request.recipe_type is not None:
        if request.recipe_type == "event_detection":
            usage_per_log += 1 if project.settings.run_event_detection else 0
        elif request.recipe_type == "sentiment_language":
            usage_per_log += 1 if project.settings.run_sentiment else 0
            usage_per_log += 1 if project.settings.run_language else 0
    else:
        if project.settings.run_event_detection:
            usage_per_log += len(project.settings.events)
        if project.settings.run_sentiment:
            usage_per_log += 1
        if project.settings.run_language:
            usage_per_log += 1

    nb_credits_used = request.nb_job_results * usage_per_log

    if config.ENVIRONMENT == "preview" or config.ENVIRONMENT == "test":
        logger.debug(
            f"Preview environment, stripe billing disabled, we would have billed {nb_credits_used} credits"
        )
        return

    if request.customer_id:
        stripe.api_key = config.STRIPE_SECRET_KEY

        stripe.billing.MeterEvent.create(
            event_name=request.meter_event_name,
            payload={
                "value": str(nb_credits_used),
                "stripe_customer_id": request.customer_id,
            },
            timestamp=int(time.time()),
        )

        logger.debug(
            f"Billed {nb_credits_used} credits to organization {request.org_id}"
        )

    elif request.org_id not in config.EXEMPTED_ORG_IDS:
        logger.error(f"Organization {request.org_id} has no stripe customer id")


@activity.defn(name="extract_langsmith_data")
async def extract_langsmith_data(
    request: PipelineLangsmithRequest,
):
    logger.info(
        f"Received LangSmith connection data for project_id: {request.project_id}"
    )
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


@activity.defn(name="extract_langfuse_data")
async def extract_langfuse_data(
    request: PipelineLangfuseRequest,
):
    logger.info(
        f"Received LangFuse connection data for project id: {request.project_id}"
    )
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


@activity.defn(name="run_recipe_on_task")
async def run_recipe_on_task(
    request: RunRecipeOnTaskRequest,
) -> dict:
    if request.tasks is None and request.tasks_ids is None:
        logger.debug("No tasks to process.")
        return {"status": "no tasks to process", "nb_job_results": 0}
    logger.info(f"Running job {request.recipe.recipe_type}")
    if request.recipe.org_id is None:
        logger.error("Recipe.org_id is missing.")
        return {"status": "error", "nb_job_results": 0}

    main_pipeline = MainPipeline(
        project_id=request.recipe.project_id,
        org_id=request.recipe.org_id,
    )

    nbr_tasks_to_process = (
        len(request.tasks)
        if request.tasks is not None
        else 0 + len(request.tasks_ids)
        if request.tasks_ids is not None
        else 0
    )

    if request.max_usage:
        if request.current_usage > request.max_usage:
            logger.warning(
                f"Org {request.org_id} has reached max usage {request.max_usage}"
            )
            return {"status": "error", "nb_job_results": 0}
        elif request.current_usage + nbr_tasks_to_process > request.max_usage:
            logger.warning(
                f"Org {request.org_id} will reach max usage {request.max_usage} with this job"
            )
            return {"status": "error", "nb_job_results": 0}

    await main_pipeline.recipe_pipeline(
        tasks=request.tasks, recipe=request.recipe, tasks_ids=request.tasks_ids
    )

    total_len = 0
    if request.tasks is not None:
        total_len += len(request.tasks)
    if request.tasks_ids is not None:
        total_len += len(request.tasks_ids)

    return {
        "status": "ok",
        "nb_job_results": total_len,
        "recipe_type": request.recipe.recipe_type,
    }


@activity.defn(name="store_opentelemetry_data")
async def store_open_telemetry_data(
    request: PipelineOpentelemetryRequest,
):
    logger.info(f"Received OpenTelemetry data for project id: {request.project_id}")
    opentelemetry_connector = OpenTelemetryConnector(
        project_id=request.project_id,
        data=request.open_telemetry_data,
    )
    return await opentelemetry_connector.process(
        org_id=request.org_id,
        current_usage=request.current_usage,
        max_usage=request.max_usage,
    )


@activity.defn(name="run_process_tasks")
async def run_process_tasks(
    request_body: TaskProcessRequest,
):
    await process_tasks_id(
        project_id=request_body.project_id,
        org_id=request_body.org_id,
        tasks_id_to_process=request_body.tasks_id_to_process,
    )
    return {
        "status": "ok",
        "nb_job_results": len(request_body.tasks_id_to_process),
    }


# The usage check for this activity is done before calling it
# Before calling it make sure that the usage is below the max_usage
@activity.defn(name="run_main_pipeline_on_messages")
async def run_main_pipeline_on_messages(
    request: RunMainPipelineOnMessagesRequest,
) -> PipelineResults | None:
    logger.info(
        f"Running main pipeline on a converation of {len(request.messages)} messages"
    )
    main_pipeline = MainPipeline(
        project_id=request.project_id,
        org_id=request.org_id,
    )
    if request.max_usage:
        if request.current_usage > request.max_usage:
            logger.warning(
                f"Org {request.org_id} has reached max usage {request.max_usage}"
            )
            return None
        elif request.current_usage + len(request.messages) > request.max_usage:
            logger.warning(
                f"Org {request.org_id} will reach max usage {request.max_usage} with this job"
            )
            return None

    await main_pipeline.set_input(messages=request.messages)
    pipeline_results = await main_pipeline.run()
    return pipeline_results


@activity.defn(name="post_main_pipeline_on_task")
async def run_main_pipeline_on_task(
    request: RunMainPipelineOnTaskRequest,
) -> PipelineResults | None:
    logger.debug(f"task: {request.task}")
    if request.task.org_id is None:
        logger.error("Task.org_id is missing.")
        return None
    if request.max_usage:
        if request.current_usage > request.max_usage:
            logger.warning(
                f"Org {request.org_id} has reached max usage {request.max_usage}"
            )
            return None
        # Only processing 1 task at a time, hence +1
        elif request.current_usage + 1 > request.max_usage:
            logger.warning(
                f"Org {request.org_id} will reach max usage {request.max_usage} with this job"
            )
            return None

    main_pipeline = MainPipeline(
        project_id=request.task.project_id,
        org_id=request.task.org_id,
    )
    pipeline_results = await main_pipeline.task_main_pipeline(task=request.task)
    return pipeline_results


@activity.defn(name="run_process_logs_for_tasks")
async def run_process_logs_for_tasks(
    request_body: LogProcessRequestForTasks,
):
    logger.info(
        f"Project {request_body.project_id} org {request_body.org_id}: processing {len(request_body.logs_to_process)} logs and saving {len(request_body.extra_logs_to_save)} extra logs."
    )
    await process_logs_for_tasks(
        project_id=request_body.project_id,
        org_id=request_body.org_id,
        logs_to_process=request_body.logs_to_process,
        extra_logs_to_save=request_body.extra_logs_to_save,
    )
    return {
        "status": "ok",
        "nb_job_results": len(request_body.logs_to_process),
    }
