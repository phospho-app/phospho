from app.api.v2.models.triggers import TriggerClusteringRequest
from app.core import config
from fastapi import APIRouter, Header, Request
from fastapi_simple_rate_limiter import rate_limiter
from app.services.mongo.ai_hub import AIHubClient
from app.services.mongo.ai_hub import ClusteringRequest
from loguru import logger
from app.db.mongo import get_mongo_db

router = APIRouter(tags=["Trigger"])


@router.post(
    "/triggers/clustering",
    description="Run the synchronisation pipeline for Langsmith and Langfuse",
    response_model=dict,
)
@rate_limiter(limit=4, seconds=60)
async def trigger_clustering(
    clustering: TriggerClusteringRequest,
    _: Request,
    key: str | None = Header(default=None),
) -> dict:
    if key != config.API_TRIGGER_SECRET:
        return {"status": "error", "message": "Invalid secret key"}
    logger.info(f"Triggering clustering for project {clustering.project_id}")
    try:
        mongo_db = await get_mongo_db()
        project = await mongo_db["projects"].find_one(
            {"id": clustering.project_id}, {"org_id": 1}
        )
        org_id = project["org_id"]

        ai_hub_client = AIHubClient(org_id=org_id, project_id=clustering.project_id)
        await ai_hub_client.run_clustering(
            clustering_request=ClusteringRequest(
                project_id=clustering.project_id,
                org_id=org_id,
                limit=clustering.limit,
                nb_credits_used=0,
            ),
            scope=clustering.scope,
        )
        return {"status": "ok", "message": "Clustering triggered successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
