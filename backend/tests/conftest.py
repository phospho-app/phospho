"""
Configuration test file of the project
Major pytest fixtures (app, db,...) are defined here
"""

import logging
import os

import pymongo
import pytest
from phospho_backend.core import config  # type: ignore
from phospho_backend.db.mongo import close_mongo_db, connect_and_init_db, get_mongo_db  # type: ignore
from phospho_backend.security.authentification import propelauth  # type: ignore
from phospho.models import Project, Task, ProjectSettings, EventDefinition
from typing import Dict, List
import phospho

# Check that we are not running the tests on the production database
assert config.ENVIRONMENT != "production"


logger = logging.getLogger(__name__)


# We redefine cleanup here to be able to run tests locally
def cleanup(
    mongo_db: pymongo.MongoClient,
    collections_to_cleanup: Dict[str, List[str]],
) -> None:
    """
    DELETE the documents in the collections specified in the collections_to_cleanup dict

    collections_to_cleanup is a dict of {collection_name: [list of ids]}
    those ids will be used to DELETE the documents in the collection
    """
    # Clean up database after the test
    if mongo_db.name != "production":
        for collection, values in collections_to_cleanup.items():
            logger.info(f"Cleaning up {len(values)} documents in {collection}")
            mongo_db[collection].delete_many({"id": {"$in": values}})
        logger.info("Database cleaned up after test")
    else:
        raise RuntimeError(
            "You are trying to clean the production database. Set MONGODB_NAME to something else than 'production'"
        )


def pytest_configure(config):
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s"
    )


@pytest.fixture(scope="session")
def mongo_db():
    mongo_db_name = os.environ["MONGODB_NAME"]
    if mongo_db_name == "production":
        raise RuntimeError(
            "You are trying to run the tests on the production database. Set MONGODB_NAME to something else than 'production'"
        )

    handler = pymongo.MongoClient(os.environ["MONGODB_URL"])
    mongo_db = handler[mongo_db_name]

    if mongo_db.name != "production":
        return mongo_db
    else:
        raise RuntimeError("You are trying to run the tests on the production database")


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


@pytest.fixture(scope="session")
def init_db():
    connect_and_init_db()
    yield
    close_mongo_db()


@pytest.fixture
def backend_url():
    # The url to the deployed backend
    return os.getenv("PHOSPHO_BACKEND_URL", "http://127.0.0.1:8000")


# Propelauth fixtures


@pytest.fixture
def org_id():
    # nico_test orga
    return os.environ["TEST_PROPELAUTH_ORG_ID"]


@pytest.fixture(scope="session")
def access_token() -> str:
    # nicolas.oulianov@phospho.app user_id in propelauth test
    user_id = os.environ["TEST_PROPELAUTH_USER_ID"]
    # Get an API token from propelauth
    token = propelauth.create_access_token(
        user_id,
        5,  # minutes of validity
    ).access_token
    return token


@pytest.fixture
def api_key():
    # phospho api_key of the test orga
    api_key = os.environ["PHOSPHO_API_KEY"]
    assert api_key is not None, "PHOSPHO_API_KEY environment variable is not set"
    return api_key


# Dummy data fixtures


@pytest.fixture
def dummy_project(mongo_db, org_id):
    dummy_project = Project(
        project_name="dummy",
        org_id=org_id,
        settings=ProjectSettings(
            events={
                "question_answering": EventDefinition(
                    org_id=org_id,
                    project_id="dummy",
                    event_name="question_answering",
                    description="The user asks a question to the assistant.",
                ),
                "webhook_trigger": EventDefinition(
                    org_id=org_id,
                    project_id="dummy",
                    event_name="webhook_trigger",
                    description="The user asks the assistant to trigger the webhook.",
                    webhook="https://webhook.site/4a272604-b59c-4297-9272-e34428e90226",
                ),
            }
        ),
    )
    mongo_db["projects"].insert_one(dummy_project.model_dump())
    yield dummy_project
    cleanup(mongo_db, {"projects": [dummy_project.id]})


@pytest.fixture
def dummy_task(mongo_db, dummy_project):
    dummy_task = Task(
        project_id=dummy_project.id,
        input="What is the weather like today?",
        output="Sunny and warm.",
    )
    mongo_db["tasks"].insert_one(dummy_task.model_dump())
    yield dummy_task
    cleanup(mongo_db, {"tasks": [dummy_task.id]})


@pytest.fixture
def populated_project(mongo_db, org_id):
    # Create the project
    populated_project = Project(
        project_name="populated",
        org_id=org_id,
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
        input="What is the weather like today and can I have a cheeseburger?",
        output="Sunny and warm.",
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


@pytest.fixture
def minimal_log_content(dummy_project):
    return [
        {"input": "test", "output": "test"},
        {
            # This log event should be ignored because it has a project_id
            # which doesn't exist
            "project_id": "baba",
            "input": "test_1",
            "output": "test",
        },
        {"input": "test_2", "output": "test", "session_id": "test"},
        {"input": "test_3", "output": "test", "session_id": "test"},
        {"input": "test_4", "output": "test", "task_id": phospho.generate_uuid()},
        # This log event should be ignored because it has an invalid task_id
        {"input": "test_5", "output": "test", "task_id": {}},
    ]
