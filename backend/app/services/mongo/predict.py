from typing import List, Any, Optional
from app.services.mongo.extractor import bill_on_stripe
from app.db.mongo import get_mongo_db
from app.db.models import JobResult
from loguru import logger
import tiktoken

from phospho.lab.models import ResultType

encoding = tiktoken.get_encoding("cl100k_base")


async def bill_input_and_output_tokens(
    org_id: str,
    input_meter_name: str,
    output_meter_name: str,
    input_tokens: int,
    output_tokens: int,
):
    await bill_on_stripe(org_id, input_tokens, input_meter_name)
    await bill_on_stripe(org_id, output_tokens, output_meter_name)
    logger.info(
        f"Billed {input_tokens} input tokens and {output_tokens} output tokens for org {org_id} ; meters: {input_meter_name} and {output_meter_name}"
    )


async def metered_prediction(
    org_id: str,
    model_id: str,
    inputs: List[Any],
    predictions: List[Any],
    project_id: Optional[str] = None,
    bill: bool = True,
) -> None:
    """
    Store the predictions in the job_results database and bill the org_id based on the model_id.

    Args:
        org_id: The organization id
        model_id: "{provider}:{model_name}"
        inputs: The inputs used for the predictions
        predictions: The predictions
        project_id: The project id
        bill: Whether to bill the org_id
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
    nb_credits_used = 0
    meter_event_name = "phospho_usage_base_meter"
    if model_id == "phospho-multimodal":
        # We bill through stripe, $10 / 1k images
        nb_credits_used = 10 * len(jobresults)

    elif model_id == "phospho:intent-embed":
        # Compute token count of input texts
        inputs_token_count = sum([len(encoding.encode(input)) for input in inputs])

        logger.debug(f"input_token_count: {inputs_token_count}")
        # We bill through stripe, $0.94 / 1M input tokens
        nb_credits_used = inputs_token_count * 94
        meter_event_name = "phospho_token_based_meter"
        logger.debug(
            f"Bill for org_id {org_id} with model_id {model_id} completed, {inputs_token_count} tokens billed"
        )

    elif (
        model_id == "openai:gpt-4o" and org_id == "818886b3-0ff7-4528-8bb9-845d5ecaa80d"
    ):
        # Bill based on the number of tokens
        # Only the orga Y has access to this model
        input_tokens = sum(
            [response["usage"]["prompt_tokens"] for response in predictions]
        )
        completion_tokens = sum(
            [response["usage"]["completion_tokens"] for response in predictions]
        )
        nb_credits_used = (input_tokens + 3 * completion_tokens) * 250
        meter_event_name = "phospho_token_based_meter"
        return None

    elif model_id == "openai:gpt-4o" or model_id == "azure:gpt-4o":
        input_tokens = sum(
            [response["usage"]["prompt_tokens"] for response in predictions]
        )
        completion_tokens = sum(
            [response["usage"]["completion_tokens"] for response in predictions]
        )
        if bill:
            await bill_input_and_output_tokens(
                org_id,
                "gpt-4o_input_tokens",
                "gpt-4o_output_tokens",
                input_tokens,
                completion_tokens,
            )
        return None

    elif model_id == "openai:gpt-4o-mini" or model_id == "azure:gpt-4o-mini":
        input_tokens = sum(
            [response["usage"]["prompt_tokens"] for response in predictions]
        )
        completion_tokens = sum(
            [response["usage"]["completion_tokens"] for response in predictions]
        )
        if bill:
            await bill_input_and_output_tokens(
                org_id,
                "gpt-4o-mini_input_tokens",
                "gpt-4o-mini_output_tokens",
                input_tokens,
                completion_tokens,
            )
        return None

    elif model_id == "mistral:mistral-small-latest":
        input_tokens = sum(
            [response["usage"]["prompt_tokens"] for response in predictions]
        )
        completion_tokens = sum(
            [response["usage"]["completion_tokens"] for response in predictions]
        )
        if bill:
            await bill_input_and_output_tokens(
                org_id,
                "mistral_small_input_tokens",
                "mistral_small_output_tokens",
                input_tokens,
                completion_tokens,
            )
        return None

    elif model_id == "mistral:mistral-large-latest":
        input_tokens = sum(
            [response["usage"]["prompt_tokens"] for response in predictions]
        )
        completion_tokens = sum(
            [response["usage"]["completion_tokens"] for response in predictions]
        )
        if bill:
            await bill_input_and_output_tokens(
                org_id,
                "mistral_large_input_tokens",
                "mistral_large_output_tokens",
                input_tokens,
                completion_tokens,
            )
        return None

    elif model_id == "phospho:tak-large":
        inputs_token_count = 0
        for input in inputs:
            for message in input.get("messages", []):
                # System messages are ignored in the tak-large endpoint
                if message["role"] != "system":
                    inputs_token_count += len(encoding.encode(message["content"]))

        outputs_token_count = sum(
            [
                len(encoding.encode(prediction["choices"][0]["message"]["content"]))
                for prediction in predictions
            ]
        )
        if bill:
            await bill_input_and_output_tokens(
                org_id,
                "tak-large_input_tokens",
                "tak-large_output_tokens",
                inputs_token_count,
                outputs_token_count,
            )
        return None

    else:
        logger.error(f"Model {model_id} not supported for metered billing")

    if bill:
        await bill_on_stripe(
            org_id=org_id,
            nb_credits_used=nb_credits_used,
            meter_event_name=meter_event_name,
        )
    return None
