from pydantic import BaseModel
from typing import Optional
from app.db.models import Comparison, Eval  # noqa: F401


class ComparisonQuery(BaseModel):
    project_id: str
    context_input: str
    old_output: str
    new_output: str
    instructions: Optional[str] = None
    test_id: Optional[str] = None
