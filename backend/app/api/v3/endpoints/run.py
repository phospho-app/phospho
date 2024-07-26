from app.api.v3.models.run import RunPipelineOnMessagesRequest
from app.security import (
    authenticate_org_key,
    get_quota_for_org,
)
from app.services.mongo.extractor import ExtractorClient
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from phospho.models import PipelineResults

router = APIRouter(tags=["Run"])


@router.post(
    "/run/main/messages",
    response_model=PipelineResults,
    description="""Run the main pipeline of a project on a task. \
Returns the events, evals, sentiment, and every other analytics enabled \
for the phospho project.

The Authorization header must be set with an API key created on the phospho platform. \
This API key must have billing enabled with a valid payment method.""",
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
