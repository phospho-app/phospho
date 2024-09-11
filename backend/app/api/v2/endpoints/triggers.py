from app.api.v2.models.triggers import TriggerClusteringRequest
from app.core import config
from fastapi import APIRouter, Header, Request
from fastapi_simple_rate_limiter import rate_limiter
from app.services.mongo.ai_hub import AIHubClient
from app.services.mongo.ai_hub import ClusteringRequest

router = APIRouter(tags=["Trigger"])


@router.post(
    "/triggers/clustering",
    description="Run the synchronisation pipeline for Langsmith and Langfuse",
    response_model=dict,
)
@rate_limiter(limit=2, seconds=60)
async def trigger_clustering(
    clustering: TriggerClusteringRequest,
    request: Request,
    key: str | None = Header(default=None),
) -> dict:
    if key != config.API_TRIGGER_SECRET:
        return {"status": "error", "message": "Invalid secret key"}
    try:
        ai_hub_client = AIHubClient(
            org_id=clustering.org_id, project_id=clustering.project_id
        )
        await ai_hub_client.run_clustering(
            clustering_request=ClusteringRequest(
                project_id=clustering.project_id,
                org_id=clustering.org_id,
                limit=clustering.limit,
                nb_credits_used=0,
            ),
            scope=request.scope,
        )
        return {"status": "ok", "message": "Clustering triggered successfully"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
