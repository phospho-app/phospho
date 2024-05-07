from fastapi import APIRouter, BackgroundTasks, Depends
from propelauth_fastapi import User

from app.api.platform.models import EventBackfillRequest
from app.security.authentification import (
    propelauth,
    verify_if_propelauth_user_can_access_project,
)
from app.services.mongo.events import run_event_detection_on_timeframe

router = APIRouter(tags=["Events"])


@router.post(
    "/events/{project_id}/run",
    response_model=dict,
    description="Run event detection on previously logged data",
)
async def post_backfill_event(
    project_id: str,
    event_backfill_request: EventBackfillRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(propelauth.require_user),
) -> dict:
    """
    Detect an event on logged data
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)
    background_tasks.add_task(
        run_event_detection_on_timeframe,
        project_id=project_id,
        event_backfill_request=event_backfill_request,
    )
    return {"status": "ok"}
