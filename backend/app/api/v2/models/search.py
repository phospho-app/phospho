from app.db.models import Task, Session
from pydantic import BaseModel
from typing import List, Optional


class SearchQuery(BaseModel):
    query: str


class SearchResponse(BaseModel):
    task_ids: Optional[List[str]] = None
    session_ids: Optional[List[str]] = None
    relevant_tasks: Optional[List[Task]] = None
    relevant_sessions: Optional[List[Session]] = None
