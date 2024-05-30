from pydantic import BaseModel
from typing import List
from phospho.models import Topic


class Topics(BaseModel):
    topics: List[Topic]
