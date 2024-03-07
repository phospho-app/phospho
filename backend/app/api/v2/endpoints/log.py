from typing import List, Union

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from loguru import logger
from pydantic import ValidationError

from app.api.v2.models import LogEvent, LogReply, LogRequest
<<<<<<< HEAD
from app.api.v2.models.log import LogError
from app.security import authenticate_org_key, verify_propelauth_org_owns_project_id
from app.security.authentification import raise_error_if_not_in_pro_tier
from app.services.mongo.log import process_log
=======
from app.security import (
    authenticate_org_key,
    verify_propelauth_org_owns_project_id,
    get_quota,
)
from app.services.mongo.extractor import run_log_process
from app.services.mongo.emails import send_quota_exceeded_email
from app.core import config
>>>>>>> dev

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
    logs_to_process: List[LogEvent] = []
    extra_logs_to_save: List[LogEvent] = []

    org_plan = await get_quota(project_id)
    current_usage = org_plan.get("current_usage", 0)
    max_usage = org_plan.get("max_usage", config.PLAN_HOBBY_MAX_NB_TASKS)

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
            # Process this log only if the usage quota is not reached
            if max_usage is None or (
                max_usage is not None and current_usage < max_usage
            ):
                logs_to_process.append(valid_log_event)
                current_usage += 1
            else:
                logger.warning(f"Max usage quota reached for project {project_id}")
                background_tasks.add_task(send_quota_exceeded_email, project_id)
                logged_events.append(
                    LogError(
                        error_in_log=f"Max usage quota reached for project {project_id}: {current_usage}/{max_usage} logs"
                    )
                )
                extra_logs_to_save.append(valid_log_event)
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
    logger.debug(
        f"Project {project_id} replying to log request with {len(logged_events)}: {len(logs_to_process)} valid logs and {len(extra_logs_to_save)} extra logs to save."
    )

    # All the tasks to process were deemed as valid and part of the usage quota
    background_tasks.add_task(
        run_log_process,
        logs_to_process=logs_to_process,
        extra_logs_to_save=extra_logs_to_save,
        project_id=project_id,
        org_id=org["org"].get("org_id"),
    )

    return log_reply
