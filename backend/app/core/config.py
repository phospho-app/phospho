"""
App configuration file
"""

import json
import os
from base64 import b64decode

from dotenv import load_dotenv
from google.oauth2 import service_account
from google.cloud.storage import Client

from loguru import logger


load_dotenv()  # take environment variables from .env.
logger.info("Loading environment variables from .env file")

### ENVIRONMENT ###
# To check if we are in production, preview, staging or test environment.
# ENV can be test, staging or production. Default: preview
ENVIRONMENT = os.getenv("ENVIRONMENT", "preview")
logger.info(f"ENVIRONMENT: {ENVIRONMENT}")

### MONGODB ###
MONGODB_URL = os.getenv("MONGODB_URL")
MONGODB_NAME = os.getenv("MONGODB_NAME")
MONGODB_MAXPOOLSIZE = 10
MONGODB_MINPOOLSIZE = 1

if ENVIRONMENT == "production" and MONGODB_NAME != "production":
    raise Exception("MONGODB_NAME is not set to 'production' in production environment")
if MONGODB_NAME == "production" and ENVIRONMENT != "production":
    raise Exception("MONGODB_NAME is set to 'production' in non-production environment")


IS_MAINTENANCE = os.getenv("IS_MAINTENANCE", "false") == "true"

### USAGE LIMITS ###
PLAN_HOBBY_MAX_NB_DETECTIONS = 10

PLAN_HOBBY_MAX_USERS = 1
PLAN_PRO_MAX_USERS = 15
PLAN_SELFHOSTED_MAX_USERS = os.getenv("PLAN_SELFHOSTED_MAX_USERS", 100)

### DOCUMENTATION ##

ADMIN_EMAIL = "notifications@phospho.app"  # Used when new users sign up

### OPENAI ###
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

### PROPELAUTH ###
PROPELAUTH_URL = os.getenv("PROPELAUTH_URL")
PROPELAUTH_API_KEY = os.getenv("PROPELAUTH_API_KEY")
if ENVIRONMENT == "test":
    PHOSPHO_ORG_ID = "3fe248a3-834c-4c26-8dcc-4e55112f702d"
else:
    PHOSPHO_ORG_ID = "13b5f728-21a5-481d-82fa-0241ca0e07b9"

### EXTRACTOR (phospho service) ###
EXTRACTOR_SECRET_KEY = os.getenv("EXTRACTOR_SECRET_KEY")
EXTRACTOR_URL = os.getenv("EXTRACTOR_URL")
# TODO: move this to a startup check
assert (
    EXTRACTOR_URL is not None
), "EXTRACTOR_URL is missing from the environment variables"

### PHOSPHO AI HUB ###
PHOSPHO_AI_HUB_URL = os.getenv("PHOSPHO_AI_HUB_URL", None)
PHOSPHO_AI_HUB_API_KEY = os.getenv("PHOSPHO_AI_HUB_API_KEY", None)
if ENVIRONMENT != "preview" and PHOSPHO_AI_HUB_URL is None:
    logger.error("PHOSPHO_AI_HUB_URL is missing from the environment variables")

### Vector Search ###
QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

### WATCHERS ###
EVALUATION_SOURCE = "phospho-6"  # If phospho
FEW_SHOT_MIN_NUMBER_OF_EXAMPLES = 10  # Make it even
# FEW_SHOT_MAX_NUMBER_OF_EXAMPLES = 50  # Imposed by Cohere API # unused

### ARGILLA SERVER (annotations) ###
ARGILLA_URL = os.getenv("ARGILLA_URL", None)
ARGILLA_API_KEY = os.getenv("ARGILLA_API_KEY", None)  # API Key with role 'owner'

MAX_NUMBER_OF_DATASET_SAMPLES = 2000
MIN_NUMBER_OF_DATASET_SAMPLES = 10

###############################################
### Config below used only in phospho cloud ###
###############################################

### SLACK ###
SLACK_URL = os.getenv("SLACK_URL")

### SENTRY ###
SENTRY_DSN = os.getenv("SENTRY_DSN")

### CICD ###
CICD_PROJECTS = ["VQcNOtKLbszDeMBVaJSr"]

### RESEND EMAILS ###
RESEND_API_KEY = os.getenv("RESEND_API_KEY")
RESEND_AUDIENCE_ID = "156e4585-8241-48ba-9ac6-9f4ffc77b955"

# Used to log event suggestions
PHOSPHO_API_KEY_ONBOARDING = os.getenv("PHOSPHO_API_KEY_ONBOARDING")

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
if ENVIRONMENT != "preview":
    assert (
        STRIPE_SECRET_KEY is not None
    ), "STRIPE_SECRET_KEY is missing from the environment variables"
else:
    STRIPE_SECRET_KEY = "NO_STRIPE_SECRET_KEY"

STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
if ENVIRONMENT != "preview":
    assert (
        STRIPE_WEBHOOK_SECRET is not None
    ), "STRIPE_WEBHOOK_SECRET is missing from the environment variables"
else:
    STRIPE_WEBHOOK_SECRET = "NO_STRIPE_WEBHOOK_SECRET"

# Needed for stripe
if ENVIRONMENT == "production":
    PHOSPHO_FRONTEND_URL = "https://platform.phospho.ai"
elif ENVIRONMENT == "staging":
    PHOSPHO_FRONTEND_URL = "https://phospho-portal.vercel.app"
else:
    PHOSPHO_FRONTEND_URL = "http://localhost:3000"

if ENVIRONMENT == "production":
    PRO_PLAN_STRIPE_PRICE_ID = "price_1PC0wPKMbS7I1rNcv09yd05H"
else:
    PRO_PLAN_STRIPE_PRICE_ID = "price_1PBxCXKMbS7I1rNclr4tic3K"

if ENVIRONMENT == "production":
    PRO_PLAN_STRIPE_PRODUCT_ID = "prod_Q256x4rqB1O2XF"
else:
    PRO_PLAN_STRIPE_PRODUCT_ID = "prod_Q21F3pwJZDvzNg"

# These orgs are exempted from the quota
EXEMPTED_ORG_IDS = [
    "13b5f728-21a5-481d-82fa-0241ca0e07b9",  # phospho
    "bb46a507-19db-4e11-bf26-6bd7cdc8dcdd",  # e
    "a5724a02-a243-4025-9b34-080f40818a31",  # m
    "144df1a7-40f6-4c8d-a0a2-9ed010c1a142",  # v
    "3bf3f4b0-2ef7-47f7-a043-d96e9f5a3d7e",  # st
    "2fdbcf01-eb52-4747-bb14-b66621973e8f",  # sa
    "5a3d67ab-231c-4ad1-adba-84b6842668ad",  # sa (a)
    "7e8f6db2-3b6b-4bf6-84ee-3f226b81e43d",  # di
]


### ANYSCALE ###
ANYSCALE_BASE_URL = "https://api.endpoints.anyscale.com/v1"
ANYSCALE_API_KEY = os.getenv("ANYSCALE_API_KEY")
if ENVIRONMENT != "preview":
    if ANYSCALE_API_KEY is None:
        logger.warning("ANYSCALE_API_KEY is missing from the environment variables")

CSV_UPLOAD_MAX_ROWS = 100000
FINE_TUNING_MINIMUM_DOCUMENTS = 20

### CRON ###
CRON_SECRET_KEY = os.getenv("CRON_SECRET_KEY")

# GCP
credentials_gcp_bucket = os.getenv("GCP_JSON_CREDENTIALS_BUCKET")
GCP_BUCKET_CLIENT = None
if credentials_gcp_bucket:
    credentials_dict = json.loads(b64decode(credentials_gcp_bucket).decode("utf-8"))
    credentials = service_account.Credentials.from_service_account_info(
        credentials_dict
    )
    GCP_BUCKET_CLIENT = Client(credentials=credentials)

### SQL DB ###
SQLDB_CONNECTION_STRING = os.getenv("SQLDB_CONNECTION_STRING")

### Customer.io
CUSTOMERIO_WRITE_KEY = os.getenv("CUSTOMERIO_WRITE_KEY")
if CUSTOMERIO_WRITE_KEY is None:
    logger.warning("CUSTOMERIO_WRITE_KEY is missing from the environment variables")
