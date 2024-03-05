import sentry_sdk
from fastapi import FastAPI

from app.api.v1.endpoints import health, pipelines
from app.core import config
from app.db.mongo import close_mongo_db, connect_and_init_db
from app.db.qdrant import close_qdrant, init_qdrant

sentry_sdk.init(
    dsn=config.EXTRACTOR_SENTRY_DSN,
    traces_sample_rate=0.1,
    profiles_sample_rate=0.1,
)
sentry_sdk.set_level("warning")

app = FastAPI()

# Event handlers
app.add_event_handler("startup", connect_and_init_db)
app.add_event_handler("startup", init_qdrant)
app.add_event_handler("shutdown", close_mongo_db)
app.add_event_handler("shutdown", close_qdrant)


API_VERSION = "v1"

app_v1 = FastAPI(
    title="phospho extractor",
    description="phospho extractor http api",
    summary="phospho extractor http api",
    version="1.0.0",
    contact={
        "name": "phospho",
        "url": "https://phospho.app",
        "email": "contact@phospho.app",
    },
)


# Attach the endpoints
app_v1.include_router(health.router, tags=["Health Check"])
app_v1.include_router(pipelines.router, tags=["Pipelines"])

app.mount("/v1", app_v1)
