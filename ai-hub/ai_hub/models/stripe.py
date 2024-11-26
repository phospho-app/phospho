from pydantic import BaseModel
from typing import Optional


class BillOnStripeRequest(BaseModel):
    org_id: str
    project_id: str
    nb_credits_used: int
    meter_event_name: str = "phospho_usage_based_meter"
    customer_id: Optional[str] = None
