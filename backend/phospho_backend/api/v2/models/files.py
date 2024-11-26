from pydantic import BaseModel


class FileUploadResponse(BaseModel):
    file_id: str
    file_name: str
    org_id: str
