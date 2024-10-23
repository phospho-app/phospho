from typing import Literal, Optional
from pydantic import BaseModel


class CreateCheckoutRequest(BaseModel):
    project_id: Optional[str] = None


class UserCreatedEventWebhook(BaseModel, extra="allow"):
    email: str
    email_confirmed: bool
    event_type: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    picture_url: Optional[str] = None
    user_id: str
    username: Optional[str] = None


class CreateDefaultProjectRequest(BaseModel):
    project_id: Optional[str] = None
    template_name: Literal["history", "animals", "medical"]


class BillingStatsRequest(BaseModel):
    usage_type: Literal[
        "event_detection",
        "clustering",
        "sentiment",
        "language",
    ]
