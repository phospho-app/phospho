from typing import List

import pandas as pd
from app.api.v2.models.log import LogEvent
from app.core.config import CSV_UPLOAD_MAX_ROWS
from app.db.models import DatasetRow
from app.db.mongo import get_mongo_db
from app.security.authorization import get_quota
from app.services.mongo.emails import send_quota_exceeded_email
from app.services.mongo.extractor import ExtractorClient
from app.utils import generate_uuid
from loguru import logger
from pydantic import ValidationError


async def process_csv_file_as_df(
    file_id: str,
    file_name: str,
    df: pd.DataFrame,
    org_id: str,
    max_rows: int = CSV_UPLOAD_MAX_ROWS,
    correct_columns: List[str] = ["text", "label", "label_text"],
):
    """
    Used for finetuning.

    "text",
    "label", # True or False
    "label_text", # A text describing the label when True (ex: The user is asking about pricing)
    """

    # Check that the csv has less than max_rows
    if len(df) > max_rows:
        logger.error(
            f"The file {file_id} of org_id {org_id} has more than {max_rows} rows. It won't be processed."
        )
        # Only get the first max_rows
        df = df.head(max_rows)

    # Check that the correct_columns are in the dataframe columns
    if not all([col in df.columns for col in correct_columns]):
        logger.error(
            f"The file {file_id} of org_id {org_id} does not have the correct columns. It won't be processed."
        )
        return

    # only keep the correct columns
    df = df[correct_columns]

    # Add the file_id to the dataframe
    df["file_id"] = file_id
    df["file_name"] = file_name
    df["org_id"] = org_id

    # Convert dataframe to list of dict
    records = df.to_dict(orient="records")

    # Validate each record with DatasetRow model
    valid_records: List[dict] = []
    for record in records:
        try:
            valid_record = DatasetRow(**record).model_dump()
            valid_records.append(valid_record)
        except ValidationError as e:
            logger.warning(f"Validation error for record {record}: {e}")
            continue

    mongo_db = await get_mongo_db()

    # Insert the valid records in the database collection datasets
    await mongo_db.datasets.insert_many(valid_records)

    logger.info(
        f"File {file_id} processed successfully, added {len(valid_records)} records."
    )


async def process_file_upload_into_log_events(
    tasks_df: pd.DataFrame, project_id: str, org_id: str
):
    """
    Used for uploading tasks.

    Columns: input, output

    Optional columns: session_id, created_at, task_id, user_id
    """

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
            tasks_df["created_at"].fillna(
                int(pd.Timestamp.now().timestamp()), inplace=True
            )
        except Exception as e:
            logger.error(f"Error converting created_at to timestamp: {e}")
            tasks_df.drop("created_at", axis=1, inplace=True)

    usage_quota = await get_quota(project_id)
    current_usage = usage_quota.current_usage
    max_usage = usage_quota.max_usage

    extractor_client = ExtractorClient(org_id=org_id, project_id=project_id)

    batch_size = 64
    for i in range(0, len(tasks_df), batch_size):
        rows = tasks_df.iloc[i : i + batch_size]
        try:
            rows_as_dict = [row.to_dict() for _, row in rows.iterrows()]
            # Replace NaN values with None
            rows_as_dict = [
                {k: v if pd.notnull(v) else None for k, v in row_as_dict.items()}
                for row_as_dict in rows_as_dict
            ]

            valid_log_events = [
                LogEvent(project_id=project_id, **row_as_dict)
                for row_as_dict in rows_as_dict
            ]

            if max_usage is None or (
                max_usage is not None
                and current_usage + len(valid_log_events) - 1 < max_usage
            ):
                current_usage += len(valid_log_events)
                # Send tasks to the extractor
                await extractor_client.run_process_log_for_tasks(
                    logs_to_process=valid_log_events,
                )
            else:
                offset = max(0, min(batch_size, max_usage - current_usage))

                extra_logs_to_save = valid_log_events[offset:]
                valid_log_events = valid_log_events[:offset]
                logger.warning(f"Max usage quota reached for project: {project_id}")
                await send_quota_exceeded_email(project_id)
                await extractor_client.run_process_log_for_tasks(
                    logs_to_process=valid_log_events,
                    extra_logs_to_save=extra_logs_to_save,
                )
        except ValidationError as e:
            logger.error(f"Error when uploading csv and LogEvent creation: {e}")
