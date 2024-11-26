import logging
from urllib.parse import urlparse

import sentry_sdk
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import phospho
from phospho_backend.api.platform import endpoints as platform_endpoints
from phospho_backend.api.v2 import endpoints as v2_endpoints
from phospho_backend.api.v3 import endpoints as v3_endpoints
from phospho_backend.core import config
from phospho_backend.db.mongo import close_mongo_db, connect_and_init_db
from phospho_backend.services.integrations import check_health_argilla

logging.info(f"ENVIRONMENT : {config.ENVIRONMENT}")


# Setup the Sentry SDK
# Ignore 400 errors in /log


def filter_events(event, _):
    url_string = event["request"]["url"]
    parsed_url = urlparse(url_string)

    if "log" in parsed_url.path.split("/"):
        status = event["response"]["status"]
        if status >= 400 and status < 500:
            return None

    return event


if config.ENVIRONMENT == "production":
    sentry_sdk.init(
        dsn=config.SENTRY_DSN,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for performance monitoring.
        traces_sample_rate=0.1,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=0.1,
        before_send=filter_events,
    )
    sentry_sdk.set_level("warning")

if config.ENVIRONMENT != "preview":
    # Used for to analyze the onboarding process
    phospho.init(
        project_id="b20659d0932d4edbb2b9682d3e6a0ccb",
        api_key=config.PHOSPHO_API_KEY_ONBOARDING,
    )
else:
    phospho.init(
        project_id="NO_PROJECT_ID",
        api_key="NO_API_KEY",
    )


tags_metadata = [
    {
        "name": "projects",
        "description": "Operations with projects. A project represent an app or an agent. Each interaction betwwen this app and a user is a session.",
    },
    {
        "name": "sessions",
        "description": "Operations with sessions. A session is meant to represent a complete interaction with a user. For instance, you can see the new chat button on ChatGPT as a way to create a new session with the conversational agent. A session is composed of tasks.",
    },
    {
        "name": "tasks",
        "description": "Operations with tasks. A task represents a specific action that the user wants to perform. For instance, in ChatGPT, a task is the generation of a new message. A task is composed of steps.",
    },
]


app = FastAPI(
    title="phospho",
    summary="phospho http api",
    version="0.0.3",
    openapi_tags=tags_metadata,
    contact={
        "name": "phospho",
        "url": "https://phospho.app",
        "email": "contact@phospho.ai",
    },
)

# Setup the CORS middleware
origins = [
    # "https://platform.phospho.ai",
    # "http://localhost",
    "*",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database

app.add_event_handler("startup", connect_and_init_db)
app.add_event_handler("shutdown", close_mongo_db)


# Other services
app.add_event_handler("startup", check_health_argilla)

# TODO: Add a healthcheck for the Argilla service, error logged if not available


# Healthcheck
@app.get("/health")
def check_health_backend():
    return {"status": "ok"}


### V2 API ###
api_v2 = FastAPI(
    title="phospho",
    summary="phospho http api v2",
    description="For more information, see the [documentation](https://docs.phospho.ai/).",
    version="0.2.1",
    contact={
        "name": "phospho",
        "url": "https://phospho.ai",
        "email": "contact@phospho.ai",
    },
)

api_v2.include_router(v2_endpoints.embeddings.router)
api_v2.include_router(v2_endpoints.log.router)
api_v2.include_router(v2_endpoints.me.router)
api_v2.include_router(v2_endpoints.models.router)
api_v2.include_router(v2_endpoints.tasks.router)
api_v2.include_router(v2_endpoints.projects.router)
api_v2.include_router(v2_endpoints.sessions.router)
api_v2.include_router(v2_endpoints.health.router)
api_v2.include_router(v2_endpoints.events.router)
api_v2.include_router(v2_endpoints.chat.router)
api_v2.include_router(v2_endpoints.cron.router)
api_v2.include_router(v2_endpoints.tak_search.router)
api_v2.include_router(v2_endpoints.triggers.router)


# Mount the subapplication on the main app with the prefix /v2/
app.mount("/v2", api_v2)
# Also mount it on /v0/ for backward compatibility
app.mount("/v0", api_v2)


### V3 API ###
api_v3 = FastAPI(
    title="phospho",
    summary="phospho http api v3",
    description="For more information, see the [documentation](https://docs.phospho.ai/).",
    version="0.3.0",
    contact={
        "name": "phospho",
        "url": "https://phospho.ai",
        "email": "contact@phospho.ai",
    },
)

api_v3.include_router(v2_endpoints.health.router, include_in_schema=False)
api_v3.include_router(v3_endpoints.log.router)
api_v3.include_router(v3_endpoints.run.router)
api_v3.include_router(v3_endpoints.export.router)

app.mount("/v3", api_v3)


### PLATEFORM ENDPOINTS ###

api_platform = FastAPI()

api_platform.include_router(platform_endpoints.integrations.router)
api_platform.include_router(platform_endpoints.debug.router)
api_platform.include_router(platform_endpoints.organizations.router)
api_platform.include_router(platform_endpoints.projects.router)
api_platform.include_router(platform_endpoints.tasks.router)
api_platform.include_router(platform_endpoints.sessions.router)
api_platform.include_router(platform_endpoints.events.router)
api_platform.include_router(platform_endpoints.explore.router)
api_platform.include_router(platform_endpoints.metadata.router)
api_platform.include_router(platform_endpoints.recipes.router)
api_platform.include_router(platform_endpoints.onboarding.router)
api_platform.include_router(platform_endpoints.clustering.router)

app.mount("/api", api_platform)
