from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from loguru import logger

from app.api.v2.models import ModelsResponse
from app.services.mongo.ai_hub import fetch_models

# Auth
from app.security.authentification import authenticate_org_key, is_org_in_alpha

router = APIRouter(tags=["models"])


@router.get(
    "/models",
    response_model=ModelsResponse,
    description="List all the models of the AI Hub available to the org",
)
def get_models(org=Depends(authenticate_org_key)):
    """
    This endpoint is used to list all the models of the AI Hub available to the org.
    Only organizations in the Alpha program can access this endpoint.
    """
    logger.info(f"Query to /models by org {org['org']['org_id']}")
    # Check that the org is in the Alpha list
    if not is_org_in_alpha(org):
        raise HTTPException(
            status_code=403,
            detail="Organization not in the Alpha program. Request access at contact@phospho.app",
        )

    return fetch_models(org_id=org["org"]["org_id"])
