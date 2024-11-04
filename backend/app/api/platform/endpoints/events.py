from app.services.mongo.recipes import (
    get_recipe_from_event_definition_id,
    run_recipe_on_tasks_batched,
)
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from loguru import logger
from propelauth_fastapi import User  # type: ignore

from app.api.platform.models import (
    EventBackfillRequest,
    Event,
    LabelRequest,
    ScoreRequest,
)
from app.security.authentification import (
    propelauth,
    verify_if_propelauth_user_can_access_project,
)
from app.services.mongo.events import (
    confirm_event,
    change_label_event,
    change_value_event,
)
from app.core import config

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
    org_id = await verify_if_propelauth_user_can_access_project(user, project_id)
    org = propelauth.fetch_org(org_id)
    org_metadata = org.get("metadata", {})
    customer_id = None

    if "customer_id" in org_metadata.keys():
        customer_id = org_metadata.get("customer_id", None)

    if (
        not customer_id
        and org_id != config.PHOSPHO_ORG_ID
        and config.ENVIRONMENT != "preview"
    ):
        raise HTTPException(
            status_code=402,
            detail="You need to add a payment method to access this service. Please update your payment details: https://platform.phospho.ai/org/settings/billing",
        )

    if isinstance(event_backfill_request.filters.created_at_end, float):
        event_backfill_request.filters.created_at_end = round(
            event_backfill_request.filters.created_at_end
        )
    if isinstance(event_backfill_request.filters.created_at_start, float):
        event_backfill_request.filters.created_at_start = round(
            event_backfill_request.filters.created_at_start
        )

    recipe = await get_recipe_from_event_definition_id(
        project_id=project_id, event_definition_id=event_backfill_request.event_id
    )
    background_tasks.add_task(
        run_recipe_on_tasks_batched,
        project_id=project_id,
        recipe=recipe,
        org_id=org_id,
        filters=event_backfill_request.filters,
        sample_rate=event_backfill_request.sample_rate,
    )
    return {"status": "ok"}


@router.post(
    "/events/{project_id}/confirm/{event_id}",
    response_model=Event,
    description="Confirm detected event",
)
async def post_confirm_event(
    project_id: str,
    event_id: str,
    user: User = Depends(propelauth.require_user),
) -> Event:
    """
    Confirm an event that was detected.
    """

    await verify_if_propelauth_user_can_access_project(user, project_id)
    event = await confirm_event(project_id=project_id, event_id=event_id)
    return event


@router.post(
    "/events/{project_id}/label/{event_id}",
    response_model=Event,
    description="Change current label of an event",
)
async def post_change_label_event(
    project_id: str,
    event_id: str,
    request: LabelRequest,
    user: User = Depends(propelauth.require_user),
) -> Event:
    """
    Change the label of an event.
    """
    logger.debug(f"Changing label of event {event_id} to {request.new_label}")
    await verify_if_propelauth_user_can_access_project(user, project_id)
    event = await change_label_event(
        project_id=project_id, event_id=event_id, new_label=request.new_label
    )
    return event


@router.post(
    "/events/{project_id}/value/{event_id}",
    response_model=Event,
    description="Change current label of an event",
)
async def post_change_value_event(
    project_id: str,
    event_id: str,
    request: ScoreRequest,
    user: User = Depends(propelauth.require_user),
) -> Event:
    """
    Change the value of a range event.
    """
    logger.debug(f"Changing value of a range event {event_id} to {request.new_value}")
    await verify_if_propelauth_user_can_access_project(user, project_id)
    event = await change_value_event(
        project_id=project_id, event_id=event_id, new_value=request.new_value
    )
    return event
