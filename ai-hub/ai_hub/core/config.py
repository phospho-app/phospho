import os
from base64 import b64decode

from dotenv import load_dotenv
from loguru import logger

load_dotenv()  # take environment variables from .env.

### ENVIRONMENT ###
# To check if we are in production or `test` environment.
# ENV can be test, staging or production. Default: preview
ENVIRONMENT = os.getenv("ENVIRONMENT", "preview")
logger.info(f"Running AI hub in environment: {ENVIRONMENT}")

### SENTRY ###
SENTRY_DSN = os.getenv("SENTRY_DSN")

### MONGODB ###
MONGODB_URL = os.getenv("MONGODB_URL")
MONGODB_NAME = os.getenv("MONGODB_NAME")
MONGODB_MAXPOOLSIZE = 10
MONGODB_MINPOOLSIZE = 1

### MOGODB COLLECTIONS NAMES ###
EMBEDDINGS_COLLECTION = "private-embeddings"
CLUSTERINGS_COLLECTION = "private-clusterings"
CLUSTERS_COLLECTION = "private-clusters"

### OPENAI ###
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
assert (
    OPENAI_API_KEY
), "No OPENAI_API_KEY found. Please set it in the environment variables."
OPENAI_EMBEDDINGS_MODEL = "text-embedding-3-small"

### STRIPE ###
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")

### RESEND ###
RESEND_API_KEY = os.getenv("RESEND_API_KEY")

# These orgs are exempted from the quota
EXEMPTED_ORG_IDS = [
    "13b5f728-21a5-481d-82fa-0241ca0e07b9",  # phospho
]

### LIMITS ###
MIN_NUMBER_OF_EMBEDDINGS_FOR_CLUSTERING = 5
TEMPORAL_MTLS_TLS_CERT_BASE64 = os.getenv("TEMPORAL_MTLS_TLS_CERT_BASE64")
TEMPORAL_MTLS_TLS_KEY_BASE64 = os.getenv("TEMPORAL_MTLS_TLS_KEY_BASE64")
TEMPORAL_MTLS_TLS_CERT = None
TEMPORAL_MTLS_TLS_KEY = None

if TEMPORAL_MTLS_TLS_CERT_BASE64 and TEMPORAL_MTLS_TLS_KEY_BASE64:
    TEMPORAL_MTLS_TLS_CERT = b64decode(TEMPORAL_MTLS_TLS_CERT_BASE64)
    TEMPORAL_MTLS_TLS_KEY = b64decode(TEMPORAL_MTLS_TLS_KEY_BASE64)
else:
    logger.warning(
        "TEMPORAL_MTLS_TLS_CERT_BASE64 or TEMPORAL_MTLS_TLS_KEY_BASE64 is missing from the environment variables"
    )
