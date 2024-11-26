import os

import resend
from loguru import logger
from propelauth_fastapi import init_auth  # type: ignore

from dotenv import load_dotenv
from tqdm import tqdm

load_dotenv()


# Check that the two env variables are set
assert (
    os.getenv("PROPELAUTH_PRODUCTION_URL") is not None
), "PROPELAUTH_PRODUCTION_URL is missing from the environment variables"
assert (
    os.getenv("PROPELAUTH_PRODUCTION_API_KEY") is not None
), "PROPELAUTH_PRODUCTION_API_KEY is missing from the environment variables"

assert (
    os.getenv("RESEND_API_KEY") is not None
), "RESEND_API_KEY is missing from the environment variables"

assert (
    os.getenv("RESEND_AUDIENCE_ID") is not None
), "RESEND_AUDIENCE_ID is missing from the environment variables"

# Init the PropelAuth client with PRODUCTION values (Read only API key is enough)
propelauth = init_auth(
    os.getenv("PROPELAUTH_PRODUCTION_URL"), os.getenv("PROPELAUTH_PRODUCTION_API_KEY")
)

logger.warning("Reading from Production")


total_users = []
page_number = 0
response = propelauth.fetch_users_by_query(
    page_size=99,
    page_number=page_number,
)
total_users.extend(response.get("users"))

while response.get("has_more_results"):
    total_users.extend(response.get("users"))
    page_number += 1
    response = propelauth.fetch_users_by_query(
        page_size=99,
        page_number=page_number,
    )

# Invert the order of the users
total_users = total_users[::-1]
logger.info(f"Number of users: {len(total_users)}")

# Set the resend API key
resend.api_key = os.environ["RESEND_API_KEY"]

emails_list = resend.Contacts.list(os.environ["RESEND_AUDIENCE_ID"])
existing_emails = [user["email"] for user in emails_list.get("data", [])]

# Remove all existing contacts from the list of users
total_users = [user for user in total_users if user["email"] not in existing_emails]


# Add each user as a contact in resend
for user in tqdm(total_users):
    if user["email"]:
        logger.info(f"Adding {user['email']} as a resend contact")
        resend.Contacts.create(
            {"email": user["email"], "audience_id": os.environ["RESEND_AUDIENCE_ID"]}
        )
