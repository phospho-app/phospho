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


class AIHubClient:
    """
    A client to interact with the AI Hub service
    """

    def __init__(
        self,
        org_id: str,
        project_id: str,
    ):
        """
        project_id: Used to gather data

        org_id: Used to bill the organization
        """
        self.org_id = org_id
        self.project_id = project_id

    async def _post(
        self,
        endpoint: str,
        data: dict,
    ) -> Optional[httpx.Response]:
        """
        Post data to an endpoint
        """
        if config.PHOSPHO_AI_HUB_URL is None:
            raise ValueError("AI Hub URL is not configured.")

        if self.org_id is None or self.project_id is None:
            raise ValueError(
                f"org_id and project_id are required, got org_id: {self.org_id} and project_id: {self.project_id}"
            )

        # We add this data for the ai hub
        data["org_id"] = self.org_id
        data["project_id"] = self.project_id

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{config.PHOSPHO_AI_HUB_URL}{endpoint}",
                    json=data,
                    headers={
                        "Authorization": f"Bearer {config.PHOSPHO_AI_HUB_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    timeout=60,
                )
                return response

        except Exception as e:
            errror_id = generate_uuid()
            error_message = f"Caught error while calling ai hub {endpoint} (error_id: {errror_id}, project_id: {self.project_id}): {e}\n{traceback.format_exception(e)}"
            logger.error(error_message)
            traceback.print_exc()
            if config.ENVIRONMENT == "production":
                if len(error_message) > 200:
                    slack_message = error_message[:200]
                else:
                    slack_message = error_message
                await slack_notification(slack_message)

        return None

    async def run_clustering(self, clustering_request: ClusteringRequest) -> None:
        """
        Call the clustering endpoint of the AI Hub
        """
        if clustering_request.scope == "messages":
            response = await self._post(
                "/v1/clusterings-messages",
                clustering_request.model_dump(mode="json"),
            )
        elif clustering_request.scope == "sessions":
            response = await self._post(
                "/v1/clusterings-sessions",
                clustering_request.model_dump(mode="json"),
            )
        else:
            raise ValueError(
                f"Invalid value for messages_or_sessions: {clustering_request.scope}"
            )

        if response is None:
            raise HTTPException(status_code=500, detail="Error while calling AI Hub")

    async def generate_embeddings(
        self, embedding_request: EmbeddingRequest
    ) -> Embedding | None:
        """
        Call the embeddings endpoint of the AI Hub
        """
        response = await self._post(
            "/v1/embeddings",
            embedding_request.model_dump(mode="json"),
        )

        return Embedding(**response.json())
