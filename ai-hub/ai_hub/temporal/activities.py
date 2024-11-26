import time
from temporalio import activity

import stripe
from ai_hub.core import config

from ai_hub.models.stripe import BillOnStripeRequest
from ai_hub.models.embeddings import EmbeddingRequest
from ai_hub.models.clusterings import ClusteringRequest
from ai_hub.services.embeddings import generate_embeddings, save_embedding
from ai_hub.services.clusterings import generate_project_clustering

from loguru import logger


@activity.defn(name="bill_on_stripe")
async def bill_on_stripe(
    request: BillOnStripeRequest,
) -> None:
    """
    Bill an organization on Stripe based on the consumption
    """
    if request.nb_credits_used == 0:
        logger.debug(f"Nothing to bill for organization {request.org_id}")
        return

    if config.ENVIRONMENT == "preview" or config.ENVIRONMENT == "test":
        logger.debug(
            f"Preview environment, stripe billing disabled, we would have billed {request.nb_credits_used} credits"
        )
        return

    if request.customer_id:
        stripe.api_key = config.STRIPE_SECRET_KEY

        stripe.billing.MeterEvent.create(
            event_name=request.meter_event_name,
            payload={
                "value": request.nb_credits_used,  # type: ignore
                "stripe_customer_id": request.customer_id,
            },
            timestamp=int(time.time()),
        )

    elif request.org_id not in config.EXEMPTED_ORG_IDS:
        logger.error(f"Organization {request.org_id} has no stripe customer id")


@activity.defn(name="create_embeddings")
async def create_embeddings(
    request: EmbeddingRequest,
):
    logger.info(
        f"Received request to generate embeddings for project {request.project_id}"
    )
    embeddings = await generate_embeddings(request)

    # Save embeddings
    await save_embedding(embeddings)

    return embeddings


@activity.defn(name="generate_clustering")
async def generate_clustering(
    request: ClusteringRequest,
):
    logger.info(
        f"Received request to generate clustering for project {request.project_id}"
    )
    await generate_project_clustering(
        project_id=request.project_id,
        org_id=request.org_id,
        limit=request.limit,
        filters=request.filters,
        model=request.model,
        scope=request.scope,
        instruction=request.instruction,
        nb_clusters=request.nb_clusters,
        clustering_mode=request.clustering_mode,
        clustering_id=request.clustering_id,
        clustering_name=request.clustering_name,
        user_email=request.user_email,
        output_format=request.output_format,
    )

    return {"status": "ok"}
