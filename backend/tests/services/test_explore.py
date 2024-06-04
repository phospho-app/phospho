import pytest
from loguru import logger

# Function to test
from app.services.mongo.explore import (
    fetch_all_clusters,
    nb_items_with_a_metadata_field,
    compute_successrate_metadata_quantiles,
    compute_nb_items_with_metadata_field,
    compute_session_length_per_metadata,
)


@pytest.mark.asyncio
async def test_main_pipeline(db, populated_project):
    async for mongo_db in db:
        test_project_id = populated_project.id

        # Run the function
        clusters = await fetch_all_clusters(test_project_id)

        logger.debug(f"Clusters: {clusters}")

        count = await nb_items_with_a_metadata_field(
            test_project_id, "tasks", "user_id"
        )

        assert count > 0

        (
            bottom_quantile,
            average,
            top_quantile,
        ) = await compute_successrate_metadata_quantiles(test_project_id, "user_id")

        logger.debug(f"Bottom quantile: {bottom_quantile}")
        logger.debug(f"Top quantile: {top_quantile}")

        assert bottom_quantile >= 0
        # assert bottom_quantile <= top_quantile

        test_project_id = populated_project.id
        test_metadata_field = "user_id"
        test_collection_name = "tasks"
        test_quantile_value = 0.1

        # Run the function
        (
            bottom_quantile,
            average,
            top_quantile,
        ) = await compute_nb_items_with_metadata_field(
            test_project_id,
            test_metadata_field,
            test_collection_name,
            test_quantile_value,
        )

        logger.debug("runned compute_nb_items_with_metadata_field")
        logger.debug(f"Bottom quantile: {bottom_quantile}")
        logger.debug(f"Average: {average}")
        logger.debug(f"Top quantile: {top_quantile}")

        assert isinstance(bottom_quantile, int)
        assert isinstance(average, float)
        assert isinstance(top_quantile, int)
        # assert bottom_quantile <= average <= top_quantile

        (
            bottom_quantile,
            average,
            top_quantile,
        ) = await compute_session_length_per_metadata(
            test_project_id,
            test_metadata_field,
            test_quantile_value,
        )
        logger.debug("runned compute_session_length_per_metadata")
        logger.debug(f"Bottom quantile: {bottom_quantile}")
        logger.debug(f"Average: {average}")
        logger.debug(f"Top quantile: {top_quantile}")

        assert isinstance(bottom_quantile, float)
        assert isinstance(average, float)
        assert isinstance(top_quantile, float)
        # assert bottom_quantile <= average <= top_quantile
