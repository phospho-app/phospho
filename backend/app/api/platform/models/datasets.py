from pydantic import BaseModel
from phospho.models import ProjectDataFilters


class DatasetCreationRequest(BaseModel):
    org_id: str
    project_id: str
    limit: int = 2000
    filters: ProjectDataFilters
