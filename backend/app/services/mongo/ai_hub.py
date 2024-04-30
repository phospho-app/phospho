"""
Interact with the AI Hub service
"""

from typing import Optional
from loguru import logger
import httpx

from app.core import config
from app.api.v2.models import (
    Model,
    ModelsResponse,
    TrainRequest,
    PredictRequest,
    PredictResponse,
)
from app.services.mongo.files import process_and_save_examples


def health_check():
    """
    Check if the extractor server is healthy
    """
    try:
        response = httpx.get(f"{config.PHOSPHO_AI_HUB_URL}/v1/health")
        return response.status_code == 200
    except Exception as e:
        logger.error(e)
        return False


async def fetch_models(org_id: Optional[str] = None) -> Optional[ModelsResponse]:
    """
    List all the models of the AI Hub
    An organization id can be provided to filter the models
    Only the models with the status "trained" are returned
    """
    async with httpx.AsyncClient() as client:
        try:
            if org_id is None:
                response = await client.get(f"{config.PHOSPHO_AI_HUB_URL}/v1/models")
            else:
                response = await client.get(
                    f"{config.PHOSPHO_AI_HUB_URL}/v1/models",
                    params={"org_id": org_id},
                    headers={
                        "Authorization": f"Bearer {config.PHOSPHO_AI_HUB_URL}",
                        "Content-Type": "application/json",
                    },
                    timeout=60,
                )
            # PArse the response
            return ModelsResponse(**response.json())

        except Exception as e:
            logger.error(e)
            return None


async def fetch_model(model_id: str) -> Model | None:
    """
    Get a model by its id
    """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                f"{config.PHOSPHO_AI_HUB_URL}/v1/models/{model_id}",
                headers={
                    "Authorization": f"Bearer {config.PHOSPHO_AI_HUB_API_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=60,
            )
            # Parse the response
            return Model(**response.json())

        except Exception as e:
            logger.error(e)
            return None


async def train_model(request_body: TrainRequest) -> Model | None:
    """
    Create a training job for a given model and dataset
    """

    # Handle the case where the dataset is passed as a list of examples
    if request_body.dataset is None and request_body.examples is not None:
        # Example mode (no dataset uploaded)
        file_id = await process_and_save_examples(
            request_body.examples, request_body.org_id
        )

    else:
        file_id = request_body.dataset

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{config.PHOSPHO_AI_HUB_URL}/v1/train",
                json={
                    "model": request_body.model,
                    "dataset": file_id,
                    "task_type": request_body.task_type,
                    "org_id": request_body.org_id,
                },
                headers={
                    "Authorization": f"Bearer {config.PHOSPHO_AI_HUB_API_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=60,
            )
            # Parse the response
            return Model(**response.json())

        except Exception as e:
            logger.error(e)
            return None


async def predict(predict_request: PredictRequest) -> PredictResponse | None:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{config.PHOSPHO_AI_HUB_URL}/v1/predict",
                json=predict_request.model_dump(),
                headers={
                    "Authorization": f"Bearer {config.PHOSPHO_AI_HUB_API_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=60,
            )
            # Parse the response
            return PredictResponse(**response.json())

        except Exception as e:
            logger.error(e)
            return None
