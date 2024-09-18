from typing import List, Optional, Literal
from phospho.models import ProjectDataFilters
from pydantic import BaseModel


class RunRecipeRequest(BaseModel):
    recipe_type_list: List[Literal["event_detection", "sentiment_language"]]
    filters: Optional[ProjectDataFilters] = None
