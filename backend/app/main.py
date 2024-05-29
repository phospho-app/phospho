import logging

import sentry_sdk
from fastapi import FastAPI, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware

import phospho
from app.core import config
from app.db.mongo import close_mongo_db, connect_and_init_db
from app.db.qdrant import close_qdrant, init_qdrant
from app.services.mongo.extractor import check_health
from app.services.mongo.ai_hub import check_health_ai_hub
from app.api.v2.endpoints.cron import run_langsmith_sync_pipeline

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.memory import MemoryJobStore

logging.info(f"ENVIRONMENT : {config.ENVIRONMENT}")


# Setup the Sentry SDK

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

# Check that the

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
        "email": "contact@phospho.app",
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

if config.ENVIRONMENT != "preview":
    app.add_event_handler("startup", init_qdrant)
    app.add_event_handler("shutdown", close_qdrant)
else:
    logging.info("Not initializing Qdrant in preview mode.")


# Other services
app.add_event_handler("startup", check_health)
app.add_event_handler("startup", check_health_ai_hub)


# Healthcheck
@app.get("/health")
def check_health():
    return {"status": "ok"}


### V2 API ###
# Following PropelAuth

from app.api.v2.endpoints import (
    evals,
    files,
    fine_tuning,
    health,
    log,
    me,
    models,
    predict,
    projects,
    sessions,
    tasks,
    tests,
    train,
    events,
    chat,
)

api_v2 = FastAPI(
    title="phospho",
    summary="phospho http api v2",
    description="For more information, see the [documentation](https://docs.phospho.ai/).",
    version="0.2.1",
    contact={
        "name": "phospho",
        "url": "https://phospho.ai",
        "email": "contact@phospho.app",
    },
)

api_v2.include_router(evals.router)
api_v2.include_router(files.router)
api_v2.include_router(fine_tuning.router)
api_v2.include_router(log.router)
api_v2.include_router(me.router)
api_v2.include_router(models.router)
api_v2.include_router(tasks.router)
api_v2.include_router(tests.router)
api_v2.include_router(predict.router)
api_v2.include_router(projects.router)
api_v2.include_router(sessions.router)
api_v2.include_router(health.router)
api_v2.include_router(events.router)
api_v2.include_router(train.router)
api_v2.include_router(chat.router)


# Mount the subapplication on the main app with the prefix /v2/
app.mount("/v2", api_v2)
# Also mount it on /v0/ for backward compatibility
app.mount("/v0", api_v2)


### PLATEFORM ENDPOINTS ###
from app.api.platform.endpoints import (
    debug,
    events,
    explore,
    metadata,
    organizations,
    projects,
    sessions,
    tasks,
)

api_platform = FastAPI()

api_platform.include_router(debug.router)
api_platform.include_router(organizations.router)
api_platform.include_router(projects.router)
api_platform.include_router(tasks.router)
api_platform.include_router(sessions.router)
api_platform.include_router(events.router)
api_platform.include_router(explore.router)
api_platform.include_router(metadata.router)

app.mount("/api", api_platform)

from app.services.mongo.cron import (
    fetch_and_decrypt_langsmith_credentials,
    encrypt_and_store_langsmith_credentials,
)

# Scheduler for cron jobs

jobstores = {
    "default": MemoryJobStore(),
}

scheduler = AsyncIOScheduler(jobstores=jobstores, timezone="Europe/Paris")
scheduler.start()


# We sync langsmith data every hour
@scheduler.scheduled_job("interval", seconds=3600)
async def run_cron_job():
    await run_langsmith_sync_pipeline()
