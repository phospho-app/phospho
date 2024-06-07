from typing import List, Any, Optional
from app.services.mongo.extractor import bill_on_stripe
from app.db.mongo import get_mongo_db
from app.db.models import JobResult
from loguru import logger
import tiktoken

from phospho.lab.models import ResultType

encoding = tiktoken.get_encoding("cl100k_base")


async def metered_prediction(
    org_id: str,
    model_id: str,
    inputs: List[Any],
    predictions: List[Any],
    project_id: Optional[str] = None,
) -> None:
    """
    Make a prediction using a model from the AI Hub and bill the organization accordingly
    model_id: "{provider}:{model_name}"
    """
    logger.debug(f"Making predictions for org_id {org_id} with model_id {model_id}")

    jobresults = []
    for pred_input, prediction in zip(inputs, predictions):
        try:
            jobresult = JobResult(
                org_id=org_id,
                project_id=project_id,
                job_id=model_id,
                value=prediction,
                result_type=ResultType.dict,
                metadata={
                    "model_id": model_id,
                    "org_id": org_id,
                    "input": pred_input,
                },
            )
            jobresults.append(jobresult)

        except Exception as e:
            logger.error(f"Error validating prediction: {e}")

    logger.debug(f"jobresults: {jobresults}")
    mongo_db = await get_mongo_db()
    mongo_db["job_results"].insert_many(
        [jobresult.model_dump() for jobresult in jobresults]
    )

    logger.info(
        f"{len(jobresults)} predictions made for org_id {org_id} with model_id {model_id}"
    )
    if model_id == "phospho-multimodal":
        # We bill through stripe, $10 / 1k images
        await bill_on_stripe(org_id, 10 * len(jobresults))
    elif model_id == "openai:gpt-4o":
        # Bill based on the number of tokens
        input_tokens = sum(
            [response["usage"]["prompt_tokens"] for response in predictions]
        )
        completion_tokens = sum(
            [response["usage"]["completion_tokens"] for response in predictions]
        )
        await bill_on_stripe(
            org_id,
            (input_tokens + 3 * completion_tokens) * 250,  # 2.5$ / 1M tokens
            meter_event_name="phospho_token_based_meter",
        )
    elif model_id == "phospho:intent-embed":
        # Compute token count of input texts
        inputs_token_count = sum([len(encoding.encode(input)) for input in inputs])

        logger.debug(f"input_token_count: {inputs_token_count}")
        # We bill through stripe, $0.50 / 1M input tokens
        await bill_on_stripe(
            org_id,
            inputs_token_count * 50,  # $0.50 / 1M input tokens
            meter_event_name="phospho_token_based_meter",
        )
        logger.debug(
            f"Bill for org_id {org_id} with model_id {model_id} completed, {inputs_token_count} tokens billed"
        )
    else:
        logger.error(f"Model {model_id} not supported for metered billing")
