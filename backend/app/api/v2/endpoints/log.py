import sys
from typing import List, Union

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from loguru import logger
from pydantic import ValidationError

from app.api.v2.models import (
    LogEvent,
    LogReply,
    LogRequest,
    LogError,
)
from app.security import (
    authenticate_org_key,
    verify_propelauth_org_owns_project_id,
    get_quota,
)
from app.services.mongo.extractor import ExtractorClient

from app.services.mongo.emails import send_quota_exceeded_email
from app.core import config

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
    """Store the batched_log_events in the logs database"""

    # Check if we are in maintenance mode
    if config.IS_MAINTENANCE:
        raise HTTPException(
            status_code=503, detail="Planned maintenance. Please try again later."
        )
    if project_id == "f9947b5baa704fd4818013718033f991":
        raise HTTPException(
            status_code=400, detail="This project is disabled for maintenance."
        )

    await verify_propelauth_org_owns_project_id(org, project_id)
    # raise_error_if_not_in_pro_tier(org)

    # We return the valid log events
    logged_events: List[Union[LogEvent, LogError]] = []

    usage_quota = await get_quota(project_id)
    current_usage = usage_quota.current_usage
    max_usage = usage_quota.max_usage

    extractor_client = ExtractorClient(
        project_id=project_id,
        org_id=org["org"].get("org_id"),
    )

    nbr_valid_logs = 0
    nbr_extra_logs = 0

    logger.info(
        f"Project {project_id} received {len(log_request.batched_log_events)} logs"
    )

    for log_event_model in log_request.batched_log_events:
        # We now validate the logs
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

            # Compute the object size in bytes
            object_size = sys.getsizeof(valid_log_event.model_dump())
            if object_size > 2_000_000:
                logger.warning(
                    f"Large log event project {project_id}: {object_size} bytes"
                    + f"\n{valid_log_event.model_dump()}"
                )

            # Process this log only if the usage quota is not reached
            if max_usage is None or (
                max_usage is not None and current_usage < max_usage
            ):
                current_usage += 1
                nbr_valid_logs += 1
                logged_events.append(valid_log_event)
                await extractor_client.run_process_log_for_tasks(
                    logs_to_process=[valid_log_event],
                )
            else:
                logger.warning(f"Max usage quota reached for project: {project_id}")
                background_tasks.add_task(send_quota_exceeded_email, project_id)
                logged_events.append(
                    LogError(
                        error_in_log=f"Max usage quota reached for project {project_id}: {current_usage}/{max_usage} logs"
                    )
                )
                nbr_extra_logs += 1
                await extractor_client.run_process_log_for_tasks(
                    logs_to_process=[],
                    extra_logs_to_save=[valid_log_event],
                )
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
        f"Project {project_id} replying to log request with {len(logged_events)}: {nbr_valid_logs} valid logs and {nbr_extra_logs} extra logs to save."
    )

    return log_reply


@router.post(
    "/log/{project_id}/opentelemetry",
    response_model=dict,
    description="Store data from OpenTelemetry in database",
)
async def store_opentelemetry_log(
    project_id: str,
    open_telemetry_data: dict,
    background_tasks: BackgroundTasks,
    org: dict = Depends(authenticate_org_key),
):
    """Store the opentelemetry data in the opentelemetry database"""

    await verify_propelauth_org_owns_project_id(org, project_id)

    extractor_client = ExtractorClient(
        project_id=project_id,
        org_id=org["org"].get("org_id"),
    )
    background_tasks.add_task(
        extractor_client.store_open_telemetry_data,
        open_telemetry_data=open_telemetry_data,
    )

    return {"status": "ok"}
