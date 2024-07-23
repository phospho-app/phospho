from typing import List, Union
from app.api.v3.models.log import LogReply, LogRequest, LogEvent, LogError
from app.core import config
from app.security import (
    authenticate_org_key,
    get_quota,
    verify_propelauth_org_owns_project_id,
)
from app.security.authorization import get_quota_for_org
from app.services.mongo.extractor import ExtractorClient
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from loguru import logger

router = APIRouter(tags=["Log"])


@router.post(
    "/log/{project_id}",
    response_model=LogReply,
    description="Store a batch of log events in database",
)
async def store_batch_of_log_events(
    log_request: LogRequest,
    background_tasks: BackgroundTasks,
    org: dict = Depends(authenticate_org_key),
) -> LogReply:
    """Store the log_content in the logs database"""

    # Check if we are in maintenance mode
    if config.IS_MAINTENANCE:
        raise HTTPException(
            status_code=503, detail="Planned maintenance. Please try again later."
        )

    await verify_propelauth_org_owns_project_id(org, log_request.project_id)
    # raise_error_if_not_in_pro_tier(org)

    # We return the valid log events
    logged_events: List[Union[LogEvent, LogError]] = []
    logs_to_process: List[LogEvent] = []
    extra_logs_to_save: List[LogEvent] = []

    usage_quota = await get_quota_for_org(org["org"].get("org_id"))
    current_usage = usage_quota.current_usage
    max_usage = usage_quota.max_usage

    for log_event_model in log_request.batched_log_events:
        # We now validate the logs
        try:
            if log_event_model.project_id is None:
                log_event_model.project_id = log_request.project_id
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
                logger.warning(f"Max usage quota reached for project: {project_id}")
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

    # All the tasks to process were deemed as valid and the org had enough credits to process them
    extractor_client = ExtractorClient(
        project_id=project_id,
        org_id=org["org"].get("org_id"),
    )
    background_tasks.add_task(
        extractor_client.run_log_process,
        logs_to_process=logs_to_process,
        extra_logs_to_save=extra_logs_to_save,
    )
    return LogReply(
        status="success",
        message="Log events stored successfully",
    )
