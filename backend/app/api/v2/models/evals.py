from pydantic import BaseModel
from typing import Optional


class ComparisonQuery(BaseModel):
    project_id: str
    context_input: str
    old_output: str
    new_output: str
    instructions: Optional[str] = None
    test_id: Optional[str] = None
