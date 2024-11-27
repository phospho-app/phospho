import os

import pymongo
import pytest
from loguru import logger

import extractor.core.config as config
from extractor.db.models import Project, Task
from extractor.db.mongo import close_mongo_db, connect_and_init_db, get_mongo_db
from tests.utils import cleanup

assert config.ENVIRONMENT != "production"


@pytest.fixture(scope="session")
async def db():
    """
    Pass this to your function that needs the db up and running
    """
    await connect_and_init_db()
    logger.info("Connected to mongodb")
    db = await get_mongo_db()
    yield db
    await close_mongo_db()
    logger.info("Disconnected from mongodb")


@pytest.fixture
def org_id():
    # nico_test orga
    return os.environ["TEST_PROPELAUTH_ORG_ID"]


@pytest.fixture(scope="session")
def mongo_db():
    mongo_db_name = config.MONGODB_NAME
    if mongo_db_name == "production":
        raise RuntimeError(
            "You are trying to run the tests on the production database. Set MONGODB_NAME to something else than 'production'"
        )

    handler = pymongo.MongoClient(config.MONGODB_URL)
    mongo_db = handler[mongo_db_name]

    if mongo_db.name != "production":
        return mongo_db
    else:
        raise RuntimeError("You are trying to run the tests on the production database")


@pytest.fixture
def dummy_project(mongo_db, org_id):
    dummy_project = Project(
        project_name="dummy",
        org_id=org_id,
        settings={
            "events": {
                "question_answering": {
                    "description": "The user asks a question to the assistant.",
                    "webhook": None,
                },
                "webhook_trigger": {
                    "description": "The user asks the assistant to trigger the webhook.",
                    "webhook": "https://webhook.site/4a272604-b59c-4297-9272-e34428e90226",
                },
            }
        },
    )
    mongo_db["projects"].insert_one(dummy_project.model_dump())
    yield dummy_project
    cleanup(mongo_db, {"projects": [dummy_project.id]})


@pytest.fixture
def populated_project(mongo_db, org_id):
    # Create the project
    populated_project = Project(
        project_name="populated",
        org_id=org_id,
        settings={
            "events": {
                "question_answering": {
                    "description": "The user asks a question to the assistant.",
                    "webhook": None,
                },
                "webhook_trigger": {
                    "description": "The user asks the assistant to trigger the webhook.",
                    "webhook": "https://webhook.site/4a272604-b59c-4297-9272-e34428e90226",
                },
            }
        },
    )
    mongo_db["projects"].insert_one(populated_project.model_dump())

    # Create the tasks
    populated_tasks = []

    dummy_task = Task(
        project_id=populated_project.id,
        input="What is the weather like today?",
        output="Sunny and warm.",
        flag="success",
        metadata={"user_id": "user_id_1"},
        org_id=org_id,
        session_id="session_id_1",
    )
    mongo_db["tasks"].insert_one(dummy_task.model_dump())
    populated_tasks.append(dummy_task)

    dummy_task = Task(
        project_id=populated_project.id,
        input="What is the weather like today and can I have a cheeseburger?",
        output="Sunny and warm.",
        flag="failure",
        metadata={"user_id": "user_id_1"},
        org_id=org_id,
        session_id="session_id_1",
    )
    mongo_db["tasks"].insert_one(dummy_task.model_dump())
    populated_tasks.append(dummy_task)

    dummy_task = Task(
        project_id=populated_project.id,
        input="Trigger the webhook please.",
        output="Done!",
        metadata={"user_id": "user_id_2"},
        org_id=org_id,
        flag="success",
        session_id="session_id_2",
    )
    mongo_db["tasks"].insert_one(dummy_task.model_dump())
    populated_tasks.append(dummy_task)

    dummy_task = Task(
        project_id=populated_project.id,
        input="What is the weather like today and can I have a cheeseburger?",
        output="Sunny and warm.",
        org_id=org_id,
    )
    mongo_db["tasks"].insert_one(dummy_task.model_dump())
    populated_tasks.append(dummy_task)

    yield populated_project

    cleanup(mongo_db, {"projects": [populated_project.id]})

    for task in populated_tasks:
        cleanup(mongo_db, {"tasks": [task.id]})
