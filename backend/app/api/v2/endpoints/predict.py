from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks

from app.api.v2.models import PredictRequest, PredictResponse
from app.security.authentification import authenticate_org_key
from app.services.mongo.ai_hub import predict
from app.services.mongo.predict import metered_prediction

router = APIRouter(tags=["Predict"])


@router.post(
    "/predict",
    response_model=PredictResponse,
    description="Generate predictions for a given model on a batch of inputs",
)
async def post_predict(
    background_tasks: BackgroundTasks,
    request_body: PredictRequest,
    org: dict = Depends(authenticate_org_key),
) -> PredictResponse:
    # Get customer_id
    org_metadata = org["org"].get("metadata", {})
    org_id = org["org"]["org_id"]
    customer_id = None

    if "customer_id" in org_metadata.keys():
        customer_id = org_metadata.get("customer_id", None)

    if not customer_id and org_id != "13b5f728-21a5-481d-82fa-0241ca0e07b9":
        raise HTTPException(
            status_code=402,
            detail="You need to add a payment method to access this service. Please update your payment details: https://platform.phospho.ai/org/settings/billing",
        )

    if (
        len(request_body.model) >= len("phospho-small")
        and request_body.model[: len("phospho-small")] == "phospho-small"
        or len(request_body.model) >= len("phospho-multimodal")
        and request_body.model[: len("phospho-multimodal")] == "phospho-multimodal"
    ):
        prediction_response = await predict(request_body)

        if prediction_response is None:
            raise HTTPException(
                status_code=500,
                detail="An error occurred while generating predictions.",
            )

        else:
            if request_body.model[: len("phospho-mutlimodal")] == "phospho-multimodal":
                if (
                    org_id != "13b5f728-21a5-481d-82fa-0241ca0e07b9"
                ):  # Only whitelisted org
                    # We bill 10 credits per image prediction
                    background_tasks.add_task(
                        metered_prediction,
                        org["org"]["org_id"],
                        request_body.model,
                        request_body.inputs,
                        prediction_response.predictions,
                    )
            return prediction_response

    else:
        raise HTTPException(
            status_code=400,
            detail="Model not supported or you don't have access to it.",
        )
