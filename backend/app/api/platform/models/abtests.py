from typing import Optional
from pydantic import BaseModel


class ABTest(BaseModel):
    version_id: Optional[str] = "None"
    score: float
    score_std: float
    nb_tasks: int
    first_task_timestamp: int


class ABTests(BaseModel):
    abtests: list[ABTest]
