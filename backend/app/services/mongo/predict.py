from typing import List
from app.services.mongo.extractor import bill_on_stripe
from app.db.mongo import get_mongo_db
from app.db.models import JobResult
from loguru import logger


async def metered_prediction(
    org_id: str, model_id: str, inputs: List[dict], predictions: List[dict]
) -> None:
    """
    Make a prediction using a model from the AI Hub and bill the organization accordingly
    """
    logger.debug(f"Making predictions for org_id {org_id} with model_id {model_id}")
    if model_id == "phospho-multimodal":
        jobresults = []
        for index in range(0, len(predictions)):
            try:
                jobresult = JobResult(
                    org_id=org_id,
                    job_id=model_id,
                    value=predictions[index],
                    result_type="dict",
                    input=inputs[index],
                )
                jobresults.append(jobresult)

            except Exception as e:
                logger.error(f"Error validating prediction: {e}")

        mongo_db = await get_mongo_db()
        mongo_db["job_results"].insert_many(
            [jobresult.model_dump() for jobresult in jobresults]
        )

        logger.info(
            f"{len(jobresults)} predictions made for org_id {org_id} with model_id {model_id}"
        )

        # We bill through stripe, $10 / 1k images
        await bill_on_stripe(org_id, 10 * len(jobresults))

    return predictions
