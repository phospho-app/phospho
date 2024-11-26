"""
In preview mode, emails are disabled.
"""

import resend
from loguru import logger
from phospho_backend.core import config
from phospho_backend.db.mongo import get_mongo_db
from phospho_backend.services.mongo.organizations import fetch_users_from_org

if config.ENVIRONMENT != "preview":
    resend.api_key = config.RESEND_API_KEY
else:
    resend.api_key = "NO_API_KEY"


def send_email(
    to_email: str,
    subject: str,
    message: str,
    from_email: str = "phospho <contact@phospho.ai>",
):
    params = {
        "from": from_email,
        "to": [to_email],
        "subject": subject,
        "html": message,
        "reply_to": "paul-louis@phospho.ai",
    }

    if config.ENVIRONMENT != "preview":
        resend.Emails.send(params)  # type: ignore
        logger.info(f"Sent email to {to_email}")


def send_welcome_email(to_email: str):
    subject = "Welcome to Phospho"
    message = """
    <html>
        <body>
            <p>Hi ,</p>
            <p>Welcome to Phospho! We are thrilled to have you onboard.</p>
            <p>Need help getting started? Want to learn more about what you can do with phospho? 
            <br> Check out <a href="https://docs.phospho.ai/guides/welcome-guide">the guides!</a></p>
            <p>If anything, feel free to reach out at paul-louis@phospho.ai or chat with our devs on <a href="https://discord.gg/BFNzpUtE">Discord.</p>
            <p>Best,
            <br>
            Paul, CEO of phospho</p>
        </body>
    </html>
    """

    params = {
        "from": "Paul from phospho <paul@phospho.ai>",
        "to": [to_email],
        "subject": subject,
        "html": message,
        "reply_to": "paul-louis@phospho.ai",
    }
    if config.ENVIRONMENT != "preview" and config.ENVIRONMENT != "test":
        logger.info(f"Sending welcome email to {to_email}")
        try:
            resend.Emails.send(params)  # type: ignore
        except Exception as e:
            logger.error(f"Error sending welcome email to {to_email}: {e}")


async def send_quota_exceeded_email(org_id: str):
    """
    Send an email to all of the users of the organization to notify them that the organization has exceeded its quota
    """
    if config.ENVIRONMENT != "preview":
        # Check if the email as already been sent : lookup in the event_emails
        mongo_db = await get_mongo_db()

        # Check the event_emails collection to see if there is a doc with org_id and event_name = "quota_exceeded"
        event_email = await mongo_db.event_emails.find_one(
            {"org_id": org_id, "event_name": "quota_exceeded"}
        )

        # If the email has already been sent
        if event_email:
            logger.debug(f"Quota exceeded email already sent to {org_id}")

        else:
            # Get all the users of the organization
            users = fetch_users_from_org(org_id)

            email_subject = "Action required: Add payment method"
            email_content = """
            <html>
                <body>
                    <p>Hello,</p>
                    <p>We're very happy that you use phospho, and we want to help you continue enjoy it.</p>
                    <p>However, it seems that your organization has exceeded its max quota. Your tasks are not analyzed</p>
                    <p>To unlock phospho full potential, you need to add a payment method.</p>
                    <ul>
                        <li>Go to <a href="https://platform.phospho.ai/org/settings/billing">your Billing settings</a></li>
                        <li>Click on the "Add payment method" button</li>
                        <li>Automatic analytics will be enabled. Enjoy <a href="https://platform.phospho.ai/org/settings/billing">advanced features!</a></li>
                    </ul>
                    <p>Feel free to reach out at <a href="mailto:paul-louis@phospho.ai">paul-louis@phospho.ai</a> if anything.</p>
                    <p>Best,</p>
                    <p>Paul, CEO of phospho</p>
                </body>
            </html>
            """

            for user in users:
                send_email(
                    user.get("email"),
                    email_subject,
                    email_content,
                    from_email="Paul from phospho <contact@phospho.ai>",
                )

            # Save the event in the event_emails collection
            await mongo_db["event_emails"].insert_one(
                {
                    "org_id": org_id,
                    "event_name": "quota_exceeded",
                    "email_subject": email_subject,
                    "email_content": email_content,
                }
            )

            logger.info(f"Sent quota exceeded email to {org_id}")


def add_email_contact(email: str):
    """
    Add an email to the contact list in Resend
    """
    if config.ENVIRONMENT == "production":
        try:
            logger.info(f"Adding {email} to the contact list")
            resend.Contacts.create(
                {
                    "email": email,
                    "audience_id": config.RESEND_AUDIENCE_ID,
                }
            )
        except Exception as e:
            logger.error(f"Error adding {email} to the contact list: {e}")


def email_user_onboarding(email: str):
    """
    Send an email to the user to onboard them
    Add them to the Resend contact list
    """
    if config.ENVIRONMENT != "preview" and config.ENVIRONMENT != "test":
        send_welcome_email(email)
        add_email_contact(email)
        logger.debug(f"finished email onboarding for {email}")


def send_payment_issue_email(to_email: str):
    if config.ENVIRONMENT != "preview":
        subject = "Action required: Activation delayed"
        message = """
        <html>
            <body>
                <p>Hello,</p>
                <p>There was an issue and we couldn't activate your account. We're sorry for the inconvenience.</p>
                <p>We are working on it and will keep you updated. If you have any questions, feel free to reach out to us at
                this email address.</p>
                <p>Best,</p>
                <p>Paul, CEO of phospho</p>
            </body>
        </html>
        """

        params = {
            "from": "Paul from phospho <paul@phospho.ai>",
            "to": [to_email],
            "subject": subject,
            "html": message,
            "reply_to": "paul-louis@phospho.ai",
        }

        resend.Emails.send(params)  # type: ignore
