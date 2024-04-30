from fastapi import APIRouter, Depends, HTTPException

from app.api.v2.models import Model, TrainRequest
from app.security.authentification import authenticate_org_key_in_alpha
from app.services.mongo.ai_hub import train_model


router = APIRouter(tags=["Train"])


@router.post(
    "/train",
    response_model=Model,
    description="Create a training job for a given model and dataset",
)
async def post_train(
    request_body: TrainRequest,
    org: dict = Depends(authenticate_org_key_in_alpha),
) -> Model:
    # Get the org id
    org_id = org["org"]["org_id"]
    request_body.org_id = org_id

    # Perform some checks
    if request_body.model == "phospho-small":
        # Check task type. For now, we only support binary classification
        if request_body.task_type != "binary-classification":
            raise HTTPException(
                status_code=400,
                detail="Task not supported. Only 'binary-classification' is supported for now.",
            )

        else:
            created_model = train_model(request_body)

            if created_model:
                return created_model

            else:
                raise HTTPException(
                    status_code=500,
                    detail="An error occurred while training the model.",
                )

    else:
        raise HTTPException(
            status_code=400,
            detail="Model not supported or you don't have access to it.",
        )
