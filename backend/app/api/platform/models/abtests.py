from typing import List, Optional
from pydantic import BaseModel


class ABTest(BaseModel):
    version_id: Optional[str] = "None"
    score: float
    score_std: Optional[float] = None
    nb_tasks: int
    first_task_timestamp: int
    confidence_interval: Optional[List[float]] = None


class ABTests(BaseModel):
    abtests: list[ABTest]
