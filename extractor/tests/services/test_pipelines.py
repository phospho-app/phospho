import pytest
from loguru import logger
from tests.utils import cleanup

from extractor.core import config
from extractor.db.models import Task
from extractor.services.pipelines import MainPipeline

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
        await MainPipeline.task_main_pipeline(dummy_task)
        logger.info("Main pipeline finished")

        # Check there is a flag
        task = await mongo_db["tasks"].find_one({"id": dummy_task.id})

        assert task["flag"] in ["success", "failure"]

        # Cleanup
        cleanup(mongo_db, {"tasks": [dummy_task.id]})
