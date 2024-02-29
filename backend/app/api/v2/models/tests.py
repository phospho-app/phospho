from pydantic import BaseModel
from typing import Optional, Literal
from app.db.models import Test


class Tests(BaseModel):
    tests: list[Test]


class TestCreationRequest(BaseModel):
    project_id: str


class TestUpdateRequest(BaseModel):
    status: Optional[Literal["started", "completed", "canceled"]] = None
    summary: Optional[dict] = None
