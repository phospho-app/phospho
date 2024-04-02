from fastapi import APIRouter, Depends

from app.api.v2.models import (
    EventDetectionReply,
    DetectEventsInTaskRequest,
    Task,
    DetectEventInMessagesRequest,
)
from app.security import (
    authenticate_org_key,
    verify_propelauth_org_owns_project_id,
)
from app.security.authentification import raise_error_if_not_in_pro_tier
from app.services.mongo.extractor import (
    run_main_pipeline_on_task,
    run_main_pipeline_on_messages,
)

router = APIRouter(tags=["Events"])


@router.post(
    "/events/{project_id}/log",
    response_model=EventDetectionReply,
    description="Detect events in a log",
)
async def post_detect_events_in_task(
    project_id: str,
    event_detection_request: DetectEventsInTaskRequest,
    org: dict = Depends(authenticate_org_key),
) -> EventDetectionReply:
    """
    Detect events in a Task
    """
    await verify_propelauth_org_owns_project_id(org, project_id)
    raise_error_if_not_in_pro_tier(org, enforce=True)

    task = Task(**event_detection_request.model_dump())
    pipeline_results = await run_main_pipeline_on_task(task)

    return EventDetectionReply(
        **event_detection_request.model_dump(),
        **pipeline_results.model_dump(),
    )


@router.post(
    "/events/{project_id}/messages",
    response_model=EventDetectionReply,
    description="Detect events in a list of messages",
)
async def post_detect_events_in_messages_list(
    project_id: str,
    event_detection_request: DetectEventInMessagesRequest,
    org: dict = Depends(authenticate_org_key),
) -> EventDetectionReply:
    """
    Detect events in a list of messages.
    We expected the list of messages to be in chronological order.
    The list of message is a continuous list of messages from a conversation.
    """
    await verify_propelauth_org_owns_project_id(org, project_id)
    raise_error_if_not_in_pro_tier(org, enforce=True)

    pipeline_results = await run_main_pipeline_on_messages(
        event_detection_request.messages,
        project_id,
    )
    return EventDetectionReply(
        **event_detection_request.model_dump(),
        events=pipeline_results.events,
    )
