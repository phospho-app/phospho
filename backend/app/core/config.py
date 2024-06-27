"""
App configuration file
"""

import os

from dotenv import load_dotenv
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
if QDRANT_URL is None:
    raise Exception("QDRANT_URL is missing from the environment variables")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
if QDRANT_API_KEY is None:
    raise Exception("QDRANT_API_KEY is missing from the environment variables")

### WATCHERS ###
EVALUATION_SOURCE = "phospho-4"  # If phospho
FEW_SHOT_MIN_NUMBER_OF_EXAMPLES = 10  # Make it even
# FEW_SHOT_MAX_NUMBER_OF_EXAMPLES = 50  # Imposed by Cohere API # unused

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
