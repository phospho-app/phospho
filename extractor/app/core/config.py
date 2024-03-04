"""
App configuration file
"""

import os
from dotenv import load_dotenv
from loguru import logger

load_dotenv()  # take environment variables from .env.
logger.info("Loading environment variables from .env file")

### ENVIRONMENT ###
# To check if we are in production or `test` environment.
# ENV can be test, staging or production. Default: test
ENVIRONMENT = os.getenv("ENVIRONMENT", "test")
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

### SECURITY ###
# Secret key for the application
EXTRACTOR_SECRET_KEY = os.getenv("EXTRACTOR_SECRET_KEY")
if not EXTRACTOR_SECRET_KEY:
    raise Exception("EXTRACTOR_SECRET_KEY is not set")
# Waiting time if the API key is wrong
API_KEY_WAITING_TIME = 0.1  # in seconds

### OPENAI ###
OPENAI_ORGANIZATION = "org-kH8tMbx6wJGWWUb3qQiLk73Z"
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

### WATCHERS ###
OPENAI_MODEL_ID = "gpt-4"  # "gpt-4"
OPENAI_MODEL_ID_FOR_EVAL = "gpt-4"
OPENAI_MODEL_ID_FOR_EVENTS = "gpt-3.5-turbo-16k"
EVALUATION_SOURCE = "phospho-4"  # If phospho
FEW_SHOT_MIN_NUMBER_OF_EXAMPLES = 10  # Make it even
FEW_SHOT_MAX_NUMBER_OF_EXAMPLES = 50  # Imposed by Cohere API

### COHERE ###
COHERE_API_KEY = os.getenv("COHERE_API_KEY")

### SENTRY ###
EXTRACTOR_SENTRY_DSN = os.getenv("EXTRACTOR_SENTRY_DSN")

RESEND_API_KEY = os.getenv("RESEND_API_KEY")
