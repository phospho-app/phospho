from typing import List, Optional, Union

from phospho_backend.api.v3.models.log import (
    LogError,
    LogReply,
    LogRequest,
    MinimalLogEventForMessages,
)
from phospho_backend.core import config
from phospho_backend.security import (
    authenticate_org_key,
    verify_propelauth_org_owns_project_id,
)
from phospho_backend.security.authorization import get_quota_for_org
from phospho_backend.services.integrations.opentelemetry import OpenTelemetryConnector
from phospho_backend.services.mongo.emails import send_quota_exceeded_email
from phospho_backend.services.mongo.extractor import ExtractorClient
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request
from loguru import logger
from opentelemetry.proto.trace.v1.trace_pb2 import TracesData  # type: ignore


router = APIRouter(tags=["Log"])


@router.post(
    "/log",
    response_model=Optional[LogReply],
    description="Store a batch of log events in database",
)
async def store_batch_of_log_events(
    log_request: LogRequest,
    background_tasks: BackgroundTasks,
    org: dict = Depends(authenticate_org_key),
) -> Optional[LogReply]:
    """Store the log_content in the logs database"""

    # Check if we are in maintenance mode
    if config.IS_MAINTENANCE:
        raise HTTPException(
            status_code=503, detail="Planned maintenance. Please try again later."
        )

    await verify_propelauth_org_owns_project_id(org, log_request.project_id)

    # We return the valid log events
    logged_events: List[Union[MinimalLogEventForMessages, LogError]] = []
    logs_to_process: List[MinimalLogEventForMessages] = []
    extra_logs_to_save: List[MinimalLogEventForMessages] = []

    usage_quota = await get_quota_for_org(org["org"].get("org_id"))
    current_usage = usage_quota.current_usage
    max_usage = usage_quota.max_usage

    for log_event_model in log_request.batched_log_events:
        # Inspect max usage quota
        if max_usage is None or (max_usage is not None and current_usage < max_usage):
            logs_to_process.append(log_event_model)
            current_usage += 1
        else:
            logger.warning(
                f"Max usage quota reached for project: {log_request.project_id}"
            )
            background_tasks.add_task(send_quota_exceeded_email, log_request.project_id)
            logged_events.append(
                LogError(
                    error_in_log=f"Max usage quota reached for project {log_request.project_id}: {current_usage}/{max_usage} logs"
                )
            )
            extra_logs_to_save.append(log_event_model)

    # All the tasks to process were deemed as valid and the org had enough credits to process them
    extractor_client = ExtractorClient(
        project_id=log_request.project_id,
        org_id=org["org"].get("org_id"),
    )
    background_tasks.add_task(
        extractor_client.run_log_process_for_messages,
        logs_to_process=logs_to_process,
        extra_logs_to_save=extra_logs_to_save,
    )

    if len(logged_events) > 0:
        return LogReply(logged_events=logged_events)

    return None


@router.post(
    "/otl/{project_id}",
    description="OpenTelemetry traces endpoint",
)
async def collect_opentelemetry_traces(
    project_id: str,
    request: Request,
    background_tasks: BackgroundTasks,
    org: dict = Depends(authenticate_org_key),
):
    """
    This endpoint is used to log traces and intermediate LLM calls to phospho.

    It's compatible with the OpenTelemetry protocol, and it's used by the OpenTelemetry SDKs to send traces to phospho.

    The traces are stored in a dedicated database and can be viewed in the phospho UI.
    """

    await verify_propelauth_org_owns_project_id(org, project_id)

    body = await request.body()
    # The data is sent as a protobuf message (python module)
    data = TracesData.FromString(body)

    connector = OpenTelemetryConnector(
        project_id=project_id,
        org_id=org["org"].get("org_id"),
    )
    background_tasks.add_task(
        connector.process,
        data=data,
    )

    return {"status": "ok"}
