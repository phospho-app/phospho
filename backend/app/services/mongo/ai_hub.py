"""
Interact with the AI Hub service
"""

from fastapi import HTTPException
import traceback
from typing import Optional

from app.services.slack import slack_notification
import httpx
from app.api.v2.models import (
    Model,
    ModelsResponse,
    Embedding,
    EmbeddingRequest,
)
from app.api.platform.models import ClusteringRequest
from app.core import config
from app.utils import generate_uuid
from loguru import logger
from app.db.mongo import get_mongo_db


async def fetch_models(org_id: Optional[str] = None) -> Optional[ModelsResponse]:
    """
    List all the models of the AI Hub
    An organization id can be provided to filter the models
    Only the models with the status "trained" are returned
    """
    mongo_db = await get_mongo_db()

    if org_id:
        # Get all the models trained by an organization
        models = (
            await mongo_db["models"]
            .find({"owned_by": org_id, "status": "trained"})
            .sort("created_at", -1)
            .to_list(length=None)
        )
        return ModelsResponse(models=models)

    else:
        models = (
            await mongo_db["models"].find({"status": "trained"}).to_list(length=None)
        )

    return ModelsResponse(models=models)


async def fetch_model(model_id: str) -> Model | None:
    """
    Get a model by its id
    """
    mongo_db = await get_mongo_db()

    model = await mongo_db["models"].find_one({"id": model_id})

    if model is None:
        raise HTTPException(status_code=404, detail="Model not found")


async def clustering(clustering_request: ClusteringRequest) -> None:
    if config.PHOSPHO_AI_HUB_URL is None:
        logger.error("AI Hub URL is not configured.")
        return
    async with httpx.AsyncClient() as client:
        try:
            if clustering_request.scope == "messages":
                _ = await client.post(
                    f"{config.PHOSPHO_AI_HUB_URL}/v1/clusterings-messages",
                    json=clustering_request.model_dump(mode="json"),
                    headers={
                        "Authorization": f"Bearer {config.PHOSPHO_AI_HUB_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    timeout=60,
                )
            elif clustering_request.scope == "sessions":
                _ = await client.post(
                    f"{config.PHOSPHO_AI_HUB_URL}/v1/clusterings-sessions",
                    json=clustering_request.model_dump(mode="json"),
                    headers={
                        "Authorization": f"Bearer {config.PHOSPHO_AI_HUB_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    timeout=60,
                )
            else:
                raise ValueError(
                    f"Invalid value for messages_or_sessions: {clustering_request.scope}"
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
