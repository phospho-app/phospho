import pandas as pd
from fastapi import UploadFile
from loguru import logger
from typing import List
from pydantic import ValidationError

from app.db.models import DatasetRow

from app.db.mongo import get_mongo_db
from app.core.config import CSV_UPLOAD_MAX_ROWS


async def process_csv_file_as_df(
    file_id: str,
    file_name: str,
    df: pd.DataFrame,
    org_id: str,
    max_rows: int = CSV_UPLOAD_MAX_ROWS,
):
    # Check that the csv has less than max_rows
    if len(df) > max_rows:
        logger.error(
            f"The file {file_id} of org_id {org_id} has more than {max_rows} rows. It won't be processed."
        )
        # Only get the first max_rows
        df = df.head(max_rows)

    correct_columns = [
        "detection_scope",
        "task_input",
        "task_output",
        "event_description",
        "label",
    ]

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
