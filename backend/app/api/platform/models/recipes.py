from typing import List, Optional
from phospho.models import ProjectDataFilters
from pydantic import BaseModel


class RunRecipeRequest(BaseModel):
    recipe_type_list: List[str]
    filters: Optional[ProjectDataFilters] = None
