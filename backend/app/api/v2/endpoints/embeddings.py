from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from app.api.v2.models import Embedding, EmbeddingRequest
from app.services.mongo.ai_hub import generate_embeddings
from app.services.mongo.predict import metered_prediction
from app.core import config

from app.security import authenticate_org_key

router = APIRouter(tags=["embeddings"])


@router.post(
    "/embeddings",
    description="Generate intent embeddings for a text",
    response_model=Embedding,
)
async def post_embeddings(
    background_tasks: BackgroundTasks,
    request_body: EmbeddingRequest,
    org: dict = Depends(authenticate_org_key),
):
    org_metadata = org["org"].get("metadata", {})
    org_id = org["org"]["org_id"]

    # Check if the organization has a payment method
    customer_id = None

    if "customer_id" in org_metadata.keys():
        customer_id = org_metadata.get("customer_id", None)

    if not customer_id and org_id != config.PHOSPHO_ORG_ID:
        raise HTTPException(
            status_code=402,
            detail="You need to add a payment method to access this service. Please update your payment details: https://platform.phospho.ai/org/settings/billing",
        )

    # Handle the emebedding model in the request
    if request_body.model != "intent-embed":
        raise HTTPException(
            status_code=400,
            detail="Model not supported. Only 'intent-embed' is supported for now.",
        )

    # Add the organization id to the request body
    request_body.org_id = org_id

    # We assume the model is "phospho-intent-embed"
    embedding = await generate_embeddings(request_body)

    if embedding is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate embeddings for the request.",
        )

    # Bill the organization for the request
    # background_tasks.add_task(save_embedding, embeddings)
    if org_id != config.PHOSPHO_ORG_ID and config.ENVIRONMENT == "production":
        background_tasks.add_task(
            metered_prediction,
            org_id=org["org"]["org_id"],
            model_id=f"phospho:{request_body.model}",
            inputs=[request_body.text],
            predictions=[embedding.model_dump()],
            project_id=request_body.project_id,
        )

    return embedding
