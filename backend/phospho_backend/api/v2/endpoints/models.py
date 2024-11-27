from fastapi import APIRouter, Depends, HTTPException
from loguru import logger

from phospho_backend.api.v2.models import Model, ModelsResponse

# Auth
from phospho_backend.security.authentification import authenticate_org_key_in_alpha
from phospho_backend.services.mongo.ai_hub import fetch_model, fetch_models

router = APIRouter(tags=["models"])


@router.get(
    "/models",
    response_model=ModelsResponse,
    description="List all the models of the AI Hub available to the org",
)
async def get_models(org=Depends(authenticate_org_key_in_alpha)):
    """
    This endpoint is used to list all the models of the AI Hub available to the org.
    Only organizations in the Alpha program can access this endpoint.
    """
    logger.info(f"Query to /models by org {org['org']['org_id']}")
    # Check that the org is in the Alpha list

    models = await fetch_models(org_id=org["org"]["org_id"])

    if models is None:
        return ModelsResponse(models=[])

    return models


@router.get(
    "/models/{model_id}",
    response_model=Model,
    description="Get a model by its id",
)
async def get_model(model_id: str, org=Depends(authenticate_org_key_in_alpha)):
    """
    This endpoint is used to get a model by its id.
    Only organizations in the Alpha program can access this endpoint.
    """
    logger.info(f"Query to /models/{model_id} by org {org['org']['org_id']}")

    # Check that the org is in the Alpha list
    fetched_model = await fetch_model(model_id)

    if fetched_model is None:
        raise HTTPException(
            status_code=404,
            detail="Model not found",
        )

    # Check the ownership of the model
    if fetched_model.owned_by is not None:
        if fetched_model.owned_by != org["org"]["org_id"]:
            raise HTTPException(
                status_code=403,
                detail="You don't have access to this model",
            )

    return fetched_model
