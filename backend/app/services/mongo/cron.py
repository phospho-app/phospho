from app.db.mongo import get_mongo_db
from app.security.authorization import get_quota
from app.services.mongo.extractor import ExtractorClient
from loguru import logger


async def fetch_projects_to_sync(type: str = "langsmith"):
    """
    Fetch the project ids to sync
    """
    mongo_db = await get_mongo_db()
    project_ids = await mongo_db["keys"].distinct("project_id", {"type": type})
    return project_ids


async def run_langsmith_sync_pipeline():
    logger.debug("Running Langsmith synchronisation pipeline")
    projects_ids = await fetch_projects_to_sync(type="langsmith")
    for project_id in projects_ids:
        usage_quota = await get_quota(project_id)
        extractor_client = ExtractorClient(
            org_id=usage_quota.org_id,
            project_id=project_id,
        )
        await extractor_client.collect_langsmith_data(
            langsmith_api_key=None,
            langsmith_project_name=None,
            current_usage=usage_quota.current_usage,
            max_usage=usage_quota.max_usage,
        )

    return {"status": "ok", "message": "Pipeline ran successfully"}


async def run_langfuse_sync_pipeline():
    logger.debug("Running Langfuse synchronisation pipeline")
    projects_ids = await fetch_projects_to_sync(type="langfuse")
    for project_id in projects_ids:
        usage_quota = await get_quota(project_id)
        extractor_client = ExtractorClient(
            org_id=usage_quota.org_id, project_id=project_id
        )
        await extractor_client.collect_langfuse_data(
            langfuse_secret_key=None,
            langfuse_public_key=None,
            current_usage=usage_quota.current_usage,
            max_usage=usage_quota.max_usage,
        )

    return {"status": "ok", "message": "Pipeline ran successfully"}
