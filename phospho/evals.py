from pydantic import BaseModel
from typing import Optional, Literal

ComparisonResults = Literal[
    "Old output is better",
    "New output is better",
    "Same quality",
    "Both are bad",
    "Error",
]


class Comparison(BaseModel):
    id: str
    created_at: int
    project_id: str
    instructions: Optional[str] = None
    context_input: str
    old_output: str
    new_output: str
    comparison_result: ComparisonResults
    source: str
