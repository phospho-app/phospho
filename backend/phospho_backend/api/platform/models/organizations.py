from typing import Literal

from pydantic import BaseModel


class CreateCheckoutRequest(BaseModel):
    project_id: str | None = None


class UserCreatedEventWebhook(BaseModel, extra="allow"):
    email: str
    email_confirmed: bool
    event_type: str
    first_name: str | None = None
    last_name: str | None = None
    picture_url: str | None = None
    user_id: str
    username: str | None = None


class CreateDefaultProjectRequest(BaseModel):
    project_id: str | None = None
    template_name: Literal["history", "animals", "medical"]


class BillingStatsRequest(BaseModel):
    usage_type: Literal[
        "event_detection",
        "clustering",
        "sentiment",
        "language",
    ]
