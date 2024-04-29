import pytest
from loguru import logger

from app.services.mongo.organizations import get_usage_quota


@pytest.mark.asyncio
async def test_org_service(db, populated_project):
    async for mongo_db in db:
        test_org_id = populated_project.org_id

        # Run the function
        usage = await get_usage_quota(test_org_id, "hobby")

        logger.debug(f"Usage: {usage}")

        assert usage.get("credits") == 0
