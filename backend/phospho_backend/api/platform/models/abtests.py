from pydantic import BaseModel


class ABTest(BaseModel):
    first_task_ts: int
    last_task_ts: int
    version_id: str | None = "None"
    score: float
    score_std: float | None = None
    nb_tasks: int
    confidence_interval: list[float] | None = None


class ABTests(BaseModel):
    abtests: list[ABTest]
