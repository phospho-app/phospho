from typing import List, Union

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from loguru import logger
from pydantic import ValidationError

from app.api.v2.models import LogEvent, LogReply, LogRequest
from app.api.v2.models.log import LogError
from app.security import authenticate_org_key, verify_propelauth_org_owns_project_id
from app.security.authentification import raise_error_if_not_in_pro_tier
from app.services.mongo.log import process_log

router = APIRouter(tags=["Logs"])


@router.post(
    "/log/{project_id}",
    response_model=LogReply,
    description="Store a batch of log events in database",
)
async def store_batch_of_log_events(
    project_id: str,
    log_request: LogRequest,
    background_tasks: BackgroundTasks,
    org: dict = Depends(authenticate_org_key),
) -> LogReply:
    """Store the log_content in the logs database"""

    await verify_propelauth_org_owns_project_id(org, project_id)
    raise_error_if_not_in_pro_tier(org)

    # We return the valid log events
    logged_events: List[Union[LogEvent, LogError]] = []
    for log_event_model in log_request.batched_log_events:
        # Validate the log in a second time, using the pydantic model
        try:
            if log_event_model.project_id is None:
                log_event_model.project_id = project_id
            else:
                # Check that the org owns the project_id
                await verify_propelauth_org_owns_project_id(
                    org, log_event_model.project_id
                )

            valid_log_event = LogEvent.model_validate(
                log_event_model.model_dump(), strict=True
            )
            logged_events.append(valid_log_event)
        except ValidationError as e:
            logger.info(f"Skip logevent processing due to validation error: {e}")
            logged_events.append(LogError(error_in_log=str(e)))
        except HTTPException as e:
            logger.info(f"Skip logevent processing due to validation error: {e}")
            logged_events.append(LogError(error_in_log=str(e)))

        except Exception as e:
            logger.warning(f"Skip logevent processing due to unknown error: {e}")
            logged_events.append(LogError(error_in_log=str(e)))

    log_reply = LogReply(logged_events=logged_events)
    background_tasks.add_task(
        process_log,
        log_reply=log_reply,
        project_id=project_id,
        org_id=org["org"].get("org_id"),
    )

    return log_reply
