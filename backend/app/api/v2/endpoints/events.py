from fastapi import APIRouter, Depends

from app.api.v2.models import EventDetectionReply, EventDetectionRequest, Task
from app.security import (
    authenticate_org_key,
    verify_propelauth_org_owns_project_id,
)
from app.security.authentification import raise_error_if_not_in_pro_tier
from app.services.mongo.extractor import run_main_pipeline

router = APIRouter(tags=["Events"])


@router.post(
    "/events/{project_id}/",
    response_model=EventDetectionRequest,
    description="Detect events in a log",
)
async def post_detect_events(
    project_id: str,
    event_detection_request: EventDetectionRequest,
    org: dict = Depends(authenticate_org_key),
) -> EventDetectionReply:
    """
    Detect events in a log
    """
    await verify_propelauth_org_owns_project_id(org, project_id)
    raise_error_if_not_in_pro_tier(org, enforce=True)

    task = Task(**event_detection_request.model_dump())
    pipeline_results = await run_main_pipeline(task)

    return EventDetectionReply(
        **event_detection_request.model_dump(),
        events=pipeline_results.events,
    )
