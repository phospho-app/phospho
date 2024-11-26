from typing import Any
from phospho_backend.core.constants import (
    RESERVED_CATEGORY_METADATA_FIELDS,
    RESERVED_NUMBER_METADATA_FIELDS,
)
import pandas as pd
from phospho_backend.api.v2.models.log import LogEvent
from phospho_backend.security.authorization import get_quota
from phospho_backend.services.mongo.emails import send_quota_exceeded_email
from phospho_backend.utils import generate_uuid
from loguru import logger
from pydantic import ValidationError
from phospho_backend.services.log import create_task_and_process_logs


async def process_file_upload_into_log_events(
    tasks_df: pd.DataFrame, project_id: str, org_id: str
):
    """
    Used for uploading tasks.

    Columns: input, output

    Optional columns: session_id, created_at, task_id, user_id
    """

    logger.debug(f"Processing file uplload into log events for project {project_id}")
    # session_id: if provided, concatenate with project_id to avoid collisions
    if "session_id" in tasks_df.columns:
        try:
            unique_sessions = tasks_df["session_id"].unique()
            # Add a unique identifier to the session_id
            new_unique_sessions = [
                f"{project_id}_{session_id}_{generate_uuid()}"
                for session_id in unique_sessions
            ]
            unique_sessions_df = pd.DataFrame(
                {"session_id": unique_sessions, "new_session_id": new_unique_sessions}
            )
            tasks_df = tasks_df.merge(unique_sessions_df, on="session_id", how="left")
            tasks_df["session_id"] = tasks_df["new_session_id"]
            tasks_df.drop("new_session_id", axis=1, inplace=True)

        except Exception as e:
            logger.error(f"Error concatenating session_id: {e}")
            tasks_df.drop("session_id", axis=1, inplace=True)

    if "task_id" in tasks_df.columns:
        try:
            tasks_df["task_id"] = tasks_df["task_id"].apply(
                lambda x: f"{project_id}_{x}_{generate_uuid()}"
            )
        except Exception as e:
            logger.error(f"Error concatenating task_id: {e}")
            tasks_df.drop("task_id", axis=1, inplace=True)

    # created_at: if provided, convert to datetime, then to timestamp
    if "created_at" in tasks_df.columns:
        try:
            tasks_df["created_at"] = pd.to_datetime(
                tasks_df["created_at"], errors="coerce"
            )
            tasks_df["created_at"] = tasks_df["created_at"].astype(int) // 10**9
            # Fill NaN values with current timestamp
            tasks_df["created_at"] = tasks_df["created_at"].fillna(
                int(pd.Timestamp.now().timestamp())
            )
        except Exception as e:
            logger.error(f"Error converting created_at to timestamp: {e}")
            tasks_df.drop("created_at", axis=1, inplace=True)

    for metadata_field in RESERVED_CATEGORY_METADATA_FIELDS:
        if metadata_field in tasks_df.columns:
            tasks_df[metadata_field] = tasks_df[metadata_field].apply(
                lambda x: str(x) if x is not None else None
            )
    for metadata_field in RESERVED_NUMBER_METADATA_FIELDS:
        if metadata_field in tasks_df.columns:

            def safe_cast_to_float(x: Any) -> Any:
                try:
                    return float(x)
                except ValueError:
                    return None

            tasks_df[metadata_field] = tasks_df[metadata_field].apply(
                # Cast only if this is castable to float
                lambda x: safe_cast_to_float(x)
            )

    usage_quota = await get_quota(project_id)
    current_usage = usage_quota.current_usage
    max_usage = usage_quota.max_usage

    # We process everything in one batch
    batch_size = tasks_df.shape[0]
    for i in range(0, len(tasks_df), batch_size):
        rows = tasks_df.iloc[i : i + batch_size]
        rows_as_dict = [row.to_dict() for _, row in rows.iterrows()]
        valid_log_events: list[LogEvent] = []
        # Replace NaN values with None
        rows_as_dict = [
            {k: v if pd.notnull(v) else None for k, v in row_as_dict.items()}
            for row_as_dict in rows_as_dict
        ]

        for row_as_dict in rows_as_dict:
            try:
                valid_log_events.append(LogEvent(project_id=project_id, **row_as_dict))
            except ValidationError as e:
                logger.error(f"Error when creating LogEvent: {e}")

        if max_usage is None or (
            max_usage is not None
            and current_usage + len(valid_log_events) - 1 < max_usage
        ):
            current_usage += len(valid_log_events)
            # Send tasks to the extractor
            await create_task_and_process_logs(
                logs_to_process=valid_log_events,
                extra_logs_to_save=[],
                project_id=project_id,
                org_id=org_id,
            )
        else:
            offset = max(0, min(batch_size, max_usage - current_usage))

            extra_logs_to_save = valid_log_events[offset:]
            valid_log_events = valid_log_events[:offset]
            logger.warning(f"Max usage quota reached for project: {project_id}")
            await send_quota_exceeded_email(project_id)
            await create_task_and_process_logs(
                logs_to_process=valid_log_events,
                extra_logs_to_save=extra_logs_to_save,
                project_id=project_id,
                org_id=org_id,
            )
