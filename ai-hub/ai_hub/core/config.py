import os
from dotenv import load_dotenv
from base64 import b64decode

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
    "bb46a507-19db-4e11-bf26-6bd7cdc8dcdd",  # e
    "a5724a02-a243-4025-9b34-080f40818a31",  # m
    "144df1a7-40f6-4c8d-a0a2-9ed010c1a142",  # v
    "3bf3f4b0-2ef7-47f7-a043-d96e9f5a3d7e",  # st
    "2fdbcf01-eb52-4747-bb14-b66621973e8f",  # sa
    "5a3d67ab-231c-4ad1-adba-84b6842668ad",  # sa (a)
    "7e8f6db2-3b6b-4bf6-84ee-3f226b81e43d",  # di
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
