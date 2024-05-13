from pydantic import BaseModel
from typing import List, Optional, Literal

from app.db.models import Task, Event, Recipe
from phospho.lab import Message
from phospho.models import SentimentObject


class RunMainPipelineOnTaskRequest(BaseModel):
    task: Task


class RunMainPipelineOnMessagesRequest(BaseModel):
    project_id: str
    messages: List[Message]


class PipelineResults(BaseModel):
    events: List[Event]
    flag: Optional[Literal["success", "failure"]]
    language: Optional[str]
    sentiment: SentimentObject


class RunRecipeOnTaskRequest(BaseModel):
    tasks: List[Task]
    recipe: Recipe
