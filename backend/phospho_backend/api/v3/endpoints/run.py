from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException
from phospho import lab
from phospho.models import PipelineResults, ProjectDataFilters
from phospho_backend.api.v3.models.run import (
    RunBacktestRequest,
    RunPipelineOnMessagesRequest,
)
from phospho_backend.security import (
    authenticate_org_key,
    get_quota_for_org,
)
from phospho_backend.services.backtest import run_backtests
from phospho_backend.services.mongo.extractor import ExtractorClient
from propelauth_py.types.user import OrgApiKeyValidation  # type: ignore

router = APIRouter(tags=["Run"])


# Need to create task objects before running the pipeline
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
    org: OrgApiKeyValidation = Depends(authenticate_org_key),
) -> PipelineResults:
    """Store the log_content in the logs database"""

    # Check the usage quota
    usage_quota = await get_quota_for_org(org.org.org_id)
    if usage_quota.plan == "hobby" or (
        usage_quota.max_usage is not None
        and usage_quota.current_usage + len(request.messages) > usage_quota.max_usage
    ):
        raise HTTPException(
            status_code=403,
            detail="Usage quota exceeded",
        )

    extractor_client = ExtractorClient(
        project_id=request.project_id,
        org_id=org.org.org_id,
    )
    # Need to create task objects before running the pipeline
    pipeline_result = await extractor_client.run_main_pipeline_on_messages(
        messages=request.messages,
    )
    return pipeline_result


@router.post(
    "/run/backtest",
    response_model=dict,
    description="Run a backtest on a project. This gathers all input messages from the project, "
    + "and calls the specified LLM with the proper system prompt. The API key used to call the LLM provider is the header OPENAI_API_KEY.",
)
async def post_run_backtests(
    body: RunBacktestRequest,
    background_tasks: BackgroundTasks,
    openai_api_key: Annotated[str, Header()],
    org: OrgApiKeyValidation = Depends(authenticate_org_key),
):
    org_id = org.org.org_id
    usage_quota = await get_quota_for_org(org_id)
    if usage_quota.plan == "hobby" or (
        usage_quota.max_usage is not None
        and usage_quota.current_usage >= usage_quota.max_usage
    ):
        raise HTTPException(
            status_code=403,
            detail="Usage quota exceeded",
        )

    if body.filters is None:
        body.filters = ProjectDataFilters()
    if body.system_prompt_variables is None:
        body.system_prompt_variables = {}

    try:
        provider, model = lab.get_provider_and_model(body.provider_and_model)
        lab.get_async_client(provider)  # type: ignore
    except NotImplementedError as e:
        raise HTTPException(status_code=400, detail=f"Invalid provider: {e}")

    background_tasks.add_task(
        run_backtests,
        system_prompt_template=body.system_prompt_template,
        system_prompt_variables=body.system_prompt_variables,
        provider_and_model=body.provider_and_model,
        version_id=body.version_id,
        project_id=body.project_id,
        org_id=org_id,
        filters=body.filters,
        openai_api_key=openai_api_key,
    )
    return {
        "message": "Backtests are running in the background.",
        "url": f"https://platform.phospho.ai/org/ab-testing?b={body.version_id}",
    }
