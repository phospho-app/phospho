from pydantic import BaseModel


class RenameClusteringRequest(BaseModel):
    clustering_id: str
    new_name: str
