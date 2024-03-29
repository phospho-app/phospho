from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, File, UploadFile

from app.security import (
    authenticate_org_key,
    verify_propelauth_org_owns_project_id,
)


router = APIRouter(tags=["Files"])


@router.post(
    "/files",
    description="Upload a file to the platform. Only csv files are supported for now.",
)
async def create_upload_file(file: UploadFile):
    if not file.filename.endswith(".csv"):
        raise HTTPException(
            status_code=400, detail="Invalid file type. Only csv files are supported."
        )
    return {"filename": file.filename}
