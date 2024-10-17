import pytest
from loguru import logger

# Function to test
from app.services.mongo.explore import fetch_all_clusters


@pytest.mark.asyncio
async def test_main_pipeline(db, populated_project):
    async for mongo_db in db:
        test_project_id = populated_project.id

        # Run the function
        clusters = await fetch_all_clusters(test_project_id)

        logger.debug(f"Clusters: {clusters}")

        logger.debug(f"Bottom quantile: {bottom_quantile}")
        logger.debug(f"Top quantile: {top_quantile}")

        assert bottom_quantile >= 0
        # assert bottom_quantile <= top_quantile

        test_project_id = populated_project.id
        test_metadata_field = "user_id"
        test_collection_name = "tasks"
        test_quantile_value = 0.1

        logger.debug(f"Bottom quantile: {bottom_quantile}")
        logger.debug(f"Average: {average}")
        logger.debug(f"Top quantile: {top_quantile}")

        assert isinstance(bottom_quantile, int)
        assert isinstance(average, float)
        assert isinstance(top_quantile, int)
        # assert bottom_quantile <= average <= top_quantile

        logger.debug(f"Bottom quantile: {bottom_quantile}")
        logger.debug(f"Average: {average}")
        logger.debug(f"Top quantile: {top_quantile}")

        assert isinstance(bottom_quantile, float)
        assert isinstance(average, float)
        assert isinstance(top_quantile, float)
        # assert bottom_quantile <= average <= top_quantile
