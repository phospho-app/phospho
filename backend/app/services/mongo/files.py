import pandas as pd
from fastapi import UploadFile
from loguru import logger

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
        return

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

    # Add the file_id to the dataframe
    df["file_id"] = file_id
    df["file_name"] = file_name
    df["org_id"] = org_id

    print(df.head())

    # mongo_db = await get_mongo_db()

    # # Insert the dataframe in the database collection datasets
    # await mongo_db.datasets.insert_many(df.to_dict(orient="records"))
