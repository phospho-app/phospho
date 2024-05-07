from fastapi import APIRouter, Depends, HTTPException

from app.api.v2.models import PredictRequest, PredictResponse
from app.security.authentification import authenticate_org_key_in_alpha
from app.services.mongo.ai_hub import predict


router = APIRouter(tags=["Predict"])


@router.post(
    "/predict",
    response_model=PredictResponse,
    description="Generate predictions for a given model on a batch of inputs",
)
async def post_predict(
    request_body: PredictRequest,
    org: dict = Depends(authenticate_org_key_in_alpha),
) -> PredictResponse:
    if (
        len(request_body.model) >= len("phospho-small")
        and request_body.model[: len("phospho-small")] == "phospho-small"
        or len(request_body.model) >= len("phospho-multimodal")
        and request_body.model[: len("phospho-multimodal")] == "phospho-multimodal"
    ):
        predictions = await predict(request_body)

        if predictions is None:
            raise HTTPException(
                status_code=500,
                detail="An error occurred while generating predictions.",
            )

        else:
            return predictions

    else:
        raise HTTPException(
            status_code=400,
            detail="Model not supported or you don't have access to it.",
        )
