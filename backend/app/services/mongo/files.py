from app.api.v2.models.log import LogEvent
from app.core import config
from app.security.authorization import get_quota
from app.services.mongo.emails import send_quota_exceeded_email
from app.services.mongo.extractor import run_log_process
import pandas as pd
from loguru import logger
from typing import List
from pydantic import ValidationError

from app.db.models import DatasetRow

from app.db.mongo import get_mongo_db
from app.core.config import CSV_UPLOAD_MAX_ROWS
from app.utils import generate_uuid


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


async def process_and_save_examples(examples: List[dict], org_id: str) -> str:
    """
    Used for finetuning.

    Process and save a list of examples
    Returns a file_id
    """
    file_id = generate_uuid(prefix="examples_")

    # Validate each record with DatasetRow model
    valid_records: List[dict] = []
    for record in examples:
        try:
            # Add the fields that are missing
            record["org_id"] = org_id
            record["file_id"] = file_id

            valid_record = DatasetRow(**record).model_dump()
            valid_records.append(valid_record)

        except ValidationError as e:
            logger.warning(f"Validation error for record {record}: {e}")
            continue

    mongo_db = await get_mongo_db()

    # Insert the valid records in the database collection datasets
    await mongo_db.datasets.insert_many(valid_records)

    logger.info(f"Processed successfully, added {len(valid_records)} records.")

    return file_id


async def process_file_upload_into_log_events(
    tasks_df: pd.DataFrame, project_id: str, org_id: str
):
    """
    Used for uploading tasks.

    Columns: input, output

    Optional columns: session_id, created_at, task_id
    """

    # session_id: if provided, concatenate with project_id to avoid collisions
    if "session_id" in tasks_df.columns:
        try:
            tasks_df["session_id"] = tasks_df["session_id"].apply(
                lambda x: f"{project_id}_{x}_{generate_uuid()}"
            )
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

    logs_to_process: List[LogEvent] = []
    extra_logs_to_save: List[LogEvent] = []

    org_plan = await get_quota(project_id)
    current_usage = org_plan.get("current_usage", 0)
    max_usage = org_plan.get("max_usage", config.PLAN_HOBBY_MAX_NB_DETECTIONS)

    for _, row in tasks_df.iterrows():
        # Create a task for each row
        try:
            valid_log_event = LogEvent(
                project_id=project_id,
                **row.to_dict(),
            )

            if max_usage is None or (
                max_usage is not None and current_usage < max_usage
            ):
                logs_to_process.append(valid_log_event)
                current_usage += 1
            else:
                logger.warning(f"Max usage quota reached for project: {project_id}")
                await send_quota_exceeded_email(project_id)
                extra_logs_to_save.append(valid_log_event)
        except ValidationError as e:
            logger.error(f"Error when uploading csv and LogEvent creation: {e}")

    # Send tasks to the extractor
    await run_log_process(
        logs_to_process=logs_to_process,
        extra_logs_to_save=extra_logs_to_save,
        project_id=project_id,
        org_id=org_id,
    )
