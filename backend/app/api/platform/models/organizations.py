from typing import Optional
from pydantic import BaseModel


class CreateCheckoutRequest(BaseModel):
    project_id: Optional[str] = None
