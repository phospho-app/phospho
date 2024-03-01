import pytest
from loguru import logger

from app.services.mongo.metadata import (
    fetch_count,
    calculate_average_for_metadata,
    calculate_top10_percent,
    calculate_bottom10_percent,
)


@pytest.mark.asyncio
async def test_fetch_count(db, populated_project):
    async for mongo_db in db:
        test_project_id = populated_project.id

        # Number of users
        nb_users = await fetch_count(test_project_id, "tasks", "user_id")

        logger.debug(f"Count : {nb_users}")

        assert nb_users > 0

        # Get the average number of tasks per user
        average_nb_tasks = await calculate_average_for_metadata(test_project_id, "tasks", "user_id")

        logger.debug(f"Average : {average_nb_tasks}")

        assert average_nb_tasks == 1.5

        # Get the top 10 tasks per user
        top10_tasks = await calculate_top10_percent(test_project_id, "tasks", "user_id")

        logger.debug(f"Top 10 : {top10_tasks}")

        assert top10_tasks == 2

        # Get the bottom 10 tasks per user
        bottom10_tasks = await calculate_bottom10_percent(test_project_id, "tasks", "user_id")

        logger.debug(f"Bottom 10 : {bottom10_tasks}")

        assert bottom10_tasks == 1
