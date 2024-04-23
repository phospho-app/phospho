from typing import Literal, Any
from loguru import logger

from app.db.models import Prediction
from app.db.mongo import get_mongo_db


async def create_prediction(
    org_id: str,
    project_id: str,
    job_id: str,
    value: Any,
    job_type: str = Literal["evaluation", "event_detection"],
    task_id: str = None,
) -> Prediction:
    """
    For now, task_id is an optional parameter
    """
    mongo_db = await get_mongo_db()

    # build the prediction object
    prediction = Prediction(
        org_id=org_id,
        project_id=project_id,
        job_id=job_id,
        value=value,
        job_type=job_type,
        task_id=task_id,
    )

    result = await mongo_db["predictions"].insert_one(prediction.model_dump())

    logger.info(
        f"Prediction created for project {project_id} and job_id {job_id} with value {value}"
    )

    return prediction
