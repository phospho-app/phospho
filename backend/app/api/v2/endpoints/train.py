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

    if request_body.dataset is None and request_body.examples is None:
        raise HTTPException(
            status_code=400,
            detail="You need to provide a dataset or a list of examples.",
        )

    if request_body.dataset is not None and request_body.examples is not None:
        raise HTTPException(
            status_code=400,
            detail="You can't provide both a dataset and a list of examples.",
        )

    # Perform some checks
    if request_body.model == "phospho-small":
        # Check task type. For now, we only support binary classification
        if request_body.task_type != "binary-classification":
            raise HTTPException(
                status_code=400,
                detail="Task not supported. Only 'binary-classification' is supported for now.",
            )

        # Check the number of examples in example mode
        if request_body.examples is not None and len(request_body.examples) < 20:
            raise HTTPException(
                status_code=400,
                detail="You need at least 20 examples to train the phospho-small model.",
            )

        else:
            created_model = await train_model(request_body)

            if created_model is not None:
                # Validate the pydantic model of the created_model object
                model_to_return = Model(**created_model.model_dump())

                return model_to_return

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
