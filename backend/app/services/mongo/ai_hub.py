"""
Interact with the AI Hub service
"""

import traceback
from typing import Optional

from app.services.slack import slack_notification
import httpx
from app.api.v2.models import (
    Model,
    ModelsResponse,
    PredictRequest,
    PredictResponse,
    TrainRequest,
    Embedding,
    EmbeddingRequest,
)
from app.api.platform.models import ClusteringRequest
from app.core import config
from app.services.mongo.files import process_and_save_examples
from app.utils import generate_uuid
from loguru import logger
from app.utils import health_check


def check_health_ai_hub():
    """
    Check if the AI Hub server is healthy
    """
    if config.PHOSPHO_AI_HUB_URL is None:
        logger.error("AI Hub URL is not configured.")
    if config.PHOSPHO_AI_HUB_API_KEY is None:
        logger.error("AI Hub API Key is not configured.")
    if (
        config.PHOSPHO_AI_HUB_URL is not None
        and config.PHOSPHO_AI_HUB_API_KEY is not None
    ):
        ai_hub_is_healthy = health_check(f"{config.PHOSPHO_AI_HUB_URL}/v1/health")
        if not ai_hub_is_healthy:
            logger.error(
                f"AI Hub server is not reachable at url {config.PHOSPHO_AI_HUB_URL}"
            )
        else:
            logger.info(
                f"AI Hub server is reachable at url {config.PHOSPHO_AI_HUB_URL}"
            )


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
                        "Authorization": f"Bearer {config.PHOSPHO_AI_HUB_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    timeout=60,
                )
            # Parse the response
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

    assert request_body.org_id is not None, "org_id is required"

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
                json=predict_request.model_dump(mode="json"),
                headers={
                    "Authorization": f"Bearer {config.PHOSPHO_AI_HUB_API_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=60,
            )
            # Parse the response
            return PredictResponse(**response.json())

        except Exception as e:
            errror_id = generate_uuid()
            error_message = f"Caught error while calling predict (error_id: {errror_id}): {e}\n{traceback.format_exception(e)}"
            logger.error(error_message)

            traceback.print_exc()
            if config.ENVIRONMENT == "production":
                if len(error_message) > 200:
                    slack_message = error_message[:200]
                else:
                    slack_message = error_message
                await slack_notification(slack_message)

            return None


async def clustering(clustering_request: ClusteringRequest) -> None:
    async with httpx.AsyncClient() as client:
        try:
            _ = await client.post(
                f"{config.PHOSPHO_AI_HUB_URL}/v1/clusterings",
                json=clustering_request.model_dump(mode="json"),
                headers={
                    "Authorization": f"Bearer {config.PHOSPHO_AI_HUB_API_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=60,
            )

        except Exception as e:
            errror_id = generate_uuid()
            error_message = f"Caught error while calling clustering (error_id: {errror_id}): {e}\n{traceback.format_exception(e)}"
            logger.error(error_message)
            traceback.print_exc()
            if config.ENVIRONMENT == "production":
                if len(error_message) > 200:
                    slack_message = error_message[:200]
                else:
                    slack_message = error_message
                await slack_notification(slack_message)


async def generate_embeddings(embedding_request: EmbeddingRequest) -> Embedding | None:
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{config.PHOSPHO_AI_HUB_URL}/v1/embeddings",
                json={
                    "text": embedding_request.input,
                    "model": embedding_request.model,
                    "org_id": embedding_request.org_id,
                    "project_id": embedding_request.project_id,
                    "task_id": embedding_request.task_id,
                },
                headers={
                    "Authorization": f"Bearer {config.PHOSPHO_AI_HUB_API_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=60,
            )
            # Parse the response
            return Embedding(**response.json())

        except Exception as e:
            logger.error(e)
            return None
