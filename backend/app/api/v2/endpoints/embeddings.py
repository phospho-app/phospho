from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from app.api.v2.models import Embedding, EmbeddingRequest
from app.services.mongo.ai_hub import generate_embeddings

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
    # Handle the emebedding model in the request
    if request_body.model != "intent-embed":
        raise HTTPException(
            status_code=400,
            detail="Model not supported. Only 'intent-embed' is supported for now.",
        )

    # We assume the model is "phospho-intent-embed"
    embedding = await generate_embeddings(request_body)

    if embedding is None:
        raise HTTPException(
            status_code=500,
            detail="Failed to generate embeddings for the request.",
        )

    # Bill the organization for the request
    # background_tasks.add_task(save_embedding, embeddings)

    return embedding
