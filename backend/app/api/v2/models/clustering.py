from pydantic import BaseModel


class ClusteringRequest(BaseModel):
    project_id: str
    org_id: str
    limit: int = 2000
