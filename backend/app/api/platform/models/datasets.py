from pydantic import BaseModel
from phospho.models import ProjectDataFilters


class DatasetCreationRequest(BaseModel):
    project_id: str
    limit: int = 2000
    workspace_id: str  # Argilla workspace id
    dataset_name: str  # Must be unique in the workspace
    filters: ProjectDataFilters
