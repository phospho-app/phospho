import pytest
import time
from loguru import logger

from app.services.pipelines import main_pipeline

from app.core import config
from app.db.models import Task

from tests.utils import cleanup

assert config.ENVIRONMENT != "production"


@pytest.mark.asyncio
async def test_main_pipeline(db, org_id, dummy_project):
    async for mongo_db in db:
        # Create a dummy task
        dummy_task = Task(
            project_id=dummy_project.id,
            input="What is the weather like today?",
            output="Sunny and warm.",
        )
        await mongo_db["tasks"].insert_one(dummy_task.model_dump())

        # Set environment variable for testing
        # test_task_id = dummy_task.id

        logger.debug("Running main pipeline on dummy task")

        logger.info("Running main pipeline")
        await main_pipeline(dummy_task)
        logger.info("Main pipeline finished")

        # Check there is a flag
        # Query the db to check the topic field of the task
        task = await mongo_db["tasks"].find_one({"id": dummy_task.id})

        assert task["flag"] in ["success", "failure"]
        # Check the topic field is not empty

        # Cleanup
        cleanup(mongo_db, {"tasks": [dummy_task.id]})
