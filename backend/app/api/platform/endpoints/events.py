from fastapi import APIRouter, BackgroundTasks, Depends

from app.api.platform.models import EventBackfillRequest
from app.security import (
    authenticate_org_key,
    verify_propelauth_org_owns_project_id,
)
from app.services.mongo.events import run_event_detection_on_timeframe

router = APIRouter(tags=["Events"])


@router.post(
    "/events/{project_id}/backfill",
    response_model=dict,
    description="Detect an event on logged data",
)
async def post_backfill_event(
    project_id: str,
    event_backfill_request: EventBackfillRequest,
    background_tasks: BackgroundTasks,
    org: dict = Depends(authenticate_org_key),
) -> dict:
    """
    Detect an event on logged data
    """
    await verify_propelauth_org_owns_project_id(org, project_id)
    background_tasks.add_task(
        run_event_detection_on_timeframe,
        project_id=project_id,
        event_backfill_request=event_backfill_request,
    )
    return {"status": "ok"}
