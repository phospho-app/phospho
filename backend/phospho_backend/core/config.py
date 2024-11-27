"""
App configuration file
"""

import json
import os
from base64 import b64decode

from dotenv import load_dotenv
from google.cloud.storage import Client  # type: ignore
from google.oauth2 import service_account
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

PLAN_HOBBY_MAX_USERS = 3
PLAN_PRO_MAX_USERS = 15
PLAN_SELFHOSTED_MAX_USERS = os.getenv("PLAN_SELFHOSTED_MAX_USERS", 100)

QUERY_MAX_LEN_LIMIT = 2000  # Limit the number of returned rows for a query to run_analytics_query() service

### DOCUMENTATION ##

ADMIN_EMAIL = "notifications@phospho.ai"  # Used when new users sign up

### OPENAI ###
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

### PROPELAUTH ###
PROPELAUTH_URL = os.getenv("PROPELAUTH_URL")
PROPELAUTH_API_KEY = os.getenv("PROPELAUTH_API_KEY")
if ENVIRONMENT == "test":
    PHOSPHO_ORG_ID = "3fe248a3-834c-4c26-8dcc-4e55112f702d"
else:
    PHOSPHO_ORG_ID = "13b5f728-21a5-481d-82fa-0241ca0e07b9"

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
# Display a nudge to annotate until this number of examples is reached
ANNOTATION_NUDGE_UNTIL_N_EXAMPLES = 10

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

TEMPORAL_HOST_URL = os.getenv("TEMPORAL_HOST_URL")
TEMPORAL_NAMESPACE = os.getenv("TEMPORAL_NAMESPACE")

try:
    TEMPORAL_MTLS_TLS_CERT: bytes | None = b64decode(
        os.environ["TEMPORAL_MTLS_TLS_CERT_BASE64"]
    )
    TEMPORAL_MTLS_TLS_KEY: bytes | None = b64decode(
        os.environ["TEMPORAL_MTLS_TLS_KEY_BASE64"]
    )
except Exception:
    logger.warning(
        "TEMPORAL_MTLS_TLS_CERT_BASE64 or TEMPORAL_MTLS_TLS_KEY_BASE64 is missing from the environment variables"
    )
    TEMPORAL_MTLS_TLS_CERT = None
    TEMPORAL_MTLS_TLS_KEY = None

API_TRIGGER_SECRET = os.getenv("API_TRIGGER_SECRET")
if API_TRIGGER_SECRET is None:
    logger.warning("API_TRIGGER_SECRET is missing from the environment variables")

# Tak Search
TAK_SEARCH_URL = os.getenv("TAK_SEARCH_URL")
if TAK_SEARCH_URL is None:
    logger.warning("TAK_SEARCH_URL is missing from the environment variables")
TAK_APP_API_KEY = os.getenv("TAK_APP_API_KEY")
if TAK_APP_API_KEY is None:
    logger.warning("TAK_APP_API_KEY is missing from the environment variables")


# Used for testing in staging or test
TEST_PROPELAUTH_ORG_ID = os.getenv("TEST_PROPELAUTH_ORG_ID")
