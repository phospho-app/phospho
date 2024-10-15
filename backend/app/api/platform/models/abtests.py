from typing import List, Optional
from pydantic import BaseModel


class ABTest(BaseModel):
    first_task_ts: int
    last_task_ts: int
    version_id: Optional[str] = "None"
    score: float
    score_std: Optional[float] = None
    nb_tasks: int
    confidence_interval: Optional[List[float]] = None


class ABTests(BaseModel):
    abtests: list[ABTest]
