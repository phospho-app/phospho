from pydantic import BaseModel, Field
from phospho.models import ProjectDataFilters
from typing import Literal, Optional, List


class DatasetSamplingParameters(BaseModel):
    """
    Parameters for sampling the dataset
    """

    sampling_type: Literal[
        "naive", "balanced"
    ]  # Naive: no sampling, Balanced: balanced sampling
    sampling_parameters: dict = Field(default_factory=dict)


class DatasetCreationRequest(BaseModel):
    project_id: str
    limit: int = 2000
    workspace_id: str  # Argilla workspace id
    dataset_name: str  # Must be unique in the workspace
    filters: ProjectDataFilters
    sampling_parameters: DatasetSamplingParameters = Field(
        default_factory=lambda: DatasetSamplingParameters(sampling_type="naive")
    )


class PostgresCredentials(BaseModel, extra="allow"):
    org_id: str
    server: str
    database: str
    username: str
    password: str
    projects_started: Optional[
        List[str]
    ] = []  # Projects that have started exporting are stored here
    projects_finished: Optional[
        List[str]
    ] = []  # Projects that have finished exporting are stored here
