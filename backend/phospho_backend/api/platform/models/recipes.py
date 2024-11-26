from typing import Literal
from phospho.models import ProjectDataFilters
from pydantic import BaseModel


class RunRecipeRequest(BaseModel):
    recipe_type_list: list[Literal["event_detection", "sentiment_language"]]
    filters: ProjectDataFilters | None = None
