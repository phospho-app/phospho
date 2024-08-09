from app.api.v3.models.run import RunBacktestRequest, RunPipelineOnMessagesRequest
from app.security import (
    authenticate_org_key,
    get_quota_for_org,
)
from app.services.backtest import run_backtests
from app.services.mongo.extractor import ExtractorClient
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from phospho.models import PipelineResults, ProjectDataFilters
from phospho import lab

router = APIRouter(tags=["Run"])


@router.post(
    "/run/main/messages",
    description="""Run the main pipeline of a project on a task. \
Returns the events, evals, sentiment, and every other analytics enabled \
for the phospho project.

The Authorization header must be set with an API key created on the phospho platform. \
This API key must have billing enabled with a valid payment method.""",
    response_model=PipelineResults,
    response_description="The pipelines results are categories of analytics. Each contain a dictionary linking an id to the result values.",
)
async def run_main_pipeline_on_messages(
    request: RunPipelineOnMessagesRequest,
    background_tasks: BackgroundTasks,
    org: dict = Depends(authenticate_org_key),
) -> PipelineResults:
    """Store the log_content in the logs database"""

    # Check the usage quota
    usage_quota = await get_quota_for_org(org["org"].get("org_id"))
    if usage_quota.plan == "hobby" or (
        usage_quota.max_usage is not None
        and usage_quota.current_usage >= usage_quota.max_usage
    ):
        raise HTTPException(
            status_code=403,
            detail="Usage quota exceeded",
        )

    extractor_client = ExtractorClient(
        project_id=request.project_id,
        org_id=org["org"].get("org_id"),
    )
    pipeline_result = await extractor_client.run_main_pipeline_on_messages(
        messages=request.messages,
    )
    return pipeline_result


@router.post(
    "/run/backtest",
    response_model=dict,
    description="Run a backtest on a project. This gathers all input messages from the project, "
    + "and calls the specified LLM with the proper system prompt.",
)
async def post_run_backtests(
    request: RunBacktestRequest,
    background_tasks: BackgroundTasks,
    org: dict = Depends(authenticate_org_key),
):
    org_id = org["org"].get("org_id")
    usage_quota = await get_quota_for_org(org_id)
    if usage_quota.plan == "hobby" or (
        usage_quota.max_usage is not None
        and usage_quota.current_usage >= usage_quota.max_usage
    ):
        raise HTTPException(
            status_code=403,
            detail="Usage quota exceeded",
        )

    if request.filters is None:
        request.filters = ProjectDataFilters()
    if request.system_prompt_variables is None:
        request.system_prompt_variables = {}

    try:
        provider, model = lab.get_provider_and_model(request.provider_and_model)
        client = lab.get_async_client(provider)
    except NotImplementedError as e:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {e}")

    background_tasks.add_task(
        run_backtests,
        system_prompt_template=request.system_prompt_template,
        system_prompt_variables=request.system_prompt_variables,
        provider_and_model=request.provider_and_model,
        version_id=request.version_id,
        project_id=request.project_id,
        org_id=org_id,
        filters=request.filters,
    )
    return {
        "message": "Backtests are running in the background.",
        "url": "https://platform.phospho.ai/org/ab-testing",
    }
