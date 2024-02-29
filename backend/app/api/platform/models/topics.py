from pydantic import BaseModel
from typing import List

class Topic(BaseModel):
    topic_name: str
    count: int

class Topics(BaseModel):
    topics: List[Topic]
