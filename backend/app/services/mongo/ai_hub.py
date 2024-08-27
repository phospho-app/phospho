"""
Interact with the AI Hub service
"""

import os
from fastapi import HTTPException
import traceback
from typing import Optional
import hashlib

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
from app.services.mongo.extractor import fetch_stripe_customer_id
from temporalio.client import Client, TLSConfig
from temporalio.exceptions import WorkflowAlreadyStartedError
from app.temporal.pydantic_converter import pydantic_data_converter


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
    else:
        return Model(**model)


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
        Post data to the ai hub temporal worker
        """

        # We check that "org_id", "project_id" are present in the data
        if self.org_id is None or self.project_id is None:
            logger.error(f"Missing org_id or project_id for endpoint {endpoint}")
            return None

        data["org_id"] = self.org_id
        data["project_id"] = self.project_id
        data["customer_id"] = await fetch_stripe_customer_id(self.org_id)

        try:
            if config.ENVIRONMENT in ["production", "staging", "test"]:
                client_cert = config.TEMPORAL_MTLS_TLS_CERT
                client_key = config.TEMPORAL_MTLS_TLS_KEY

                client: Client = await Client.connect(
                    os.getenv("TEMPORAL_HOST_URL"),
                    namespace=os.getenv("TEMPORAL_NAMESPACE"),
                    tls=TLSConfig(
                        client_cert=client_cert,
                        client_private_key=client_key,
                    ),
                    data_converter=pydantic_data_converter,
                )
            elif config.ENVIRONMENT == "preview":
                client: Client = await Client.connect(
                    os.getenv("TEMPORAL_HOST_URL"),
                    namespace=os.getenv("TEMPORAL_NAMESPACE"),
                    tls=False,
                    data_converter=pydantic_data_converter,
                )
            else:
                raise ValueError(f"Unknown environment {config.ENVIRONMENT}")

            # Hash the data to generate a unique determinist id
            unique_id = (
                endpoint
                + hashlib.md5(
                    repr(sorted(data.items())).encode("utf-8"),
                    usedforsecurity=False,
                ).hexdigest()
            )

            await client.execute_workflow(
                endpoint, data, id=unique_id, task_queue="default"
            )

        except WorkflowAlreadyStartedError as e:
            logger.warning(
                f"Workflow {endpoint} has already started for project {self.project_id} in org {self.org_id}: {e}"
            )

        except Exception as e:
            error_id = generate_uuid()
            error_message = (
                f"Caught error while calling temporal workflow {endpoint} "
                + f"(error_id: {error_id} project_id: {self.project_id} organisation_id: {self.org_id}):"
                + f"{e}\n{traceback.format_exception(e)}"
            )
            logger.error(error_message)

            traceback.print_exc()
            if config.ENVIRONMENT == "production":
                if len(error_message) > 800:
                    slack_message = error_message[:800]
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
                "generate_clustering_messages_workflow",
                clustering_request.model_dump(mode="json"),
            )
        elif clustering_request.scope == "sessions":
            response = await self._post(
                "generate_clustering_sessions_workflow",
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
            "create_embeddings_workflow",
            embedding_request.model_dump(mode="json"),
        )

        return Embedding(**response.json())
