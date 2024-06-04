from pydantic import BaseModel
from typing import List
from phospho.models import Cluster


class Clusters(BaseModel):
    clusters: List[Cluster]
