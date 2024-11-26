import logging
import os
from typing import Callable

import resend
from organizations import fetch_users_from_org
from pydantic import BaseModel, Field
from utils import generate_timestamp

logger = logging.getLogger(__name__)

# Set the resend API key

resend.api_key = os.getenv("RESEND_API_KEY")


# Define the structure of the document for the database
class EmailEventlModel(BaseModel):
    created_at: int = Field(default_factory=generate_timestamp)
    event_name: str
    org_id: str
    email_subject: str
    email_content: str


class EmailEvent:
    def __init__(
        self,
        event_name: str,
        email_subject: str,
        email_content: str,
        is_true_for_org: Callable[[str], bool],
    ) -> None:
        """
        :is_true_for_org: Takes as argument a verifier function that takes an org_id in arguement and returns a boolean
        """
        self.event_name = event_name
        self.email_subject = email_subject
        self.email_content = email_content
        self.is_true_for_org = is_true_for_org

    def send_email(self, org_id: str):
        """
        Sends the event email to all the users of the organization
        """
        # Get all the users of the organization
        users = fetch_users_from_org(org_id)

        for user in users:
            logger.info(
                f"Sending email to {user.get('email')} for event {self.event_name}"
            )
            # Send the email
            params = {
                "from": "phospho <notifications@phospho.ai>",
                "to": [user.get("email")],
                "subject": self.email_subject,
                "html": self.email_content,
                "reply_to": "contact@phospho.ai",
            }

            resend.Emails.send(params)
