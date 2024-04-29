"""
Interact with the AI Hub service
"""

from loguru import logger
import httpx

from app.core import config
from app.api.v2.models import Model, ModelsResponse, TrainRequest


def health_check():
    """
    Check if the extractor server is healthy
    """
    try:
        response = httpx.get(f"{config.PROPRIETARY_AI_HUB_URL}/v1/health")
        return response.status_code == 200
    except Exception as e:
        logger.error(e)
        return False


def fetch_models(org_id: str = None) -> ModelsResponse:
    """
    List all the models of the AI Hub
    An organization id can be provided to filter the models
    Only the models with the status "trained" are returned
    """
    try:
        if org_id is None:
            response = httpx.get(f"{config.PROPRIETARY_AI_HUB_URL}/v1/models")
        else:
            response = httpx.get(
                f"{config.PROPRIETARY_AI_HUB_URL}/v1/models",
                params={"org_id": org_id},
                headers={
                    "Authorization": f"Bearer {config.PROPRIETARY_AI_HUB_API_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=60,
            )
        # PArse the response
        return ModelsResponse(**response.json())

    except Exception as e:
        logger.error(e)
        return False


def fetch_model(model_id: str) -> Model | None:
    """
    Get a model by its id
    """
    try:
        response = httpx.get(
            f"{config.PROPRIETARY_AI_HUB_URL}/v1/models/{model_id}",
            headers={
                "Authorization": f"Bearer {config.PROPRIETARY_AI_HUB_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=60,
        )
        # Parse the response
        return Model(**response.json())

    except Exception as e:
        logger.error(e)
        return None


def train_model(request_body: TrainRequest) -> Model | None:
    """
    Create a training job for a given model and dataset
    """
    try:
        response = httpx.post(
            f"{config.PROPRIETARY_AI_HUB_URL}/v1/train",
            json=request_body.model_dump(),
            headers={
                "Authorization": f"Bearer {config.PROPRIETARY_AI_HUB_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=60,
        )
        # Parse the response
        return Model(**response.json())

    except Exception as e:
        logger.error(e)
        return None
