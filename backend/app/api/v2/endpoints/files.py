from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile
from loguru import logger
import pandas as pd

from app.security import (
    authenticate_org_key,
)
from app.utils import generate_uuid
from app.services.mongo.files import process_csv_file_as_df
from app.api.v2.models.files import FileUploadResponse


router = APIRouter(tags=["Files"])


@router.post(
    "/files",
    description="Upload a file to the platform. Only csv files are supported for now.",
    response_model=FileUploadResponse,
)
async def create_upload_file(
    file: UploadFile,
    background_tasks: BackgroundTasks,
    org: dict = Depends(authenticate_org_key),
):
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400, detail="Invalid file type. Only csv files are supported."
        )

    # Create a file id and store the file in the database
    file_id = generate_uuid(prefix="file_")
    file_name = file.filename
    org_id = org["org"].get("org_id")

    # Read file content -> into memory
    df = pd.read_csv(file.file)

    logger.info(f"File {file_id} uploaded successfully.")

    # Process the csv file as a background task
    background_tasks.add_task(process_csv_file_as_df, file_id, file_name, df, org_id)

    logger.debug(f"File {file_id} queued for processing.")

    return FileUploadResponse(file_id=file_id, file_name=file_name, org_id=org_id)
