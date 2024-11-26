from phospho_backend.db.mongo import get_mongo_db
from phospho_backend.security.authorization import get_quota
from phospho_backend.services.integrations.postgresql import (
    PostgresqlIntegration,
    PostgresqlCredentials,
)
from phospho_backend.services.mongo.extractor import ExtractorClient
from phospho_backend.services.mongo.projects import get_project_by_id
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

    return {"status": "ok"}


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

    return {"status": "ok"}


async def run_postgresql_sync_pipeline():
    mongo_db = await get_mongo_db()
    integrations = (
        await mongo_db["integrations"].find({"type": "postgresql"}).to_list(length=None)
    )

    for integration in integrations:
        try:
            valid_integration = PostgresqlCredentials.model_validate(integration)
            project_list = valid_integration.projects_finished
            for project_id in project_list:
                project = await get_project_by_id(project_id)
                postgresql_integration = PostgresqlIntegration(
                    org_id=valid_integration.org_id,
                    org_name=valid_integration.org_name,
                    project_id=project.id,
                    project_name=project.project_name,
                )
                await postgresql_integration.push()
        except Exception as e:
            logger.error(
                f"Error running postgresql sync pipeline {integration.get('org_id')}: {e}"
            )
    return {"status": "ok"}
