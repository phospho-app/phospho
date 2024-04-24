from typing import Any, Dict, List, Optional, cast
from app.core import config

from app.db.models import Comparison, ComparisonResults, Eval, Test
from app.db.mongo import get_mongo_db
from app.utils import generate_timestamp
from fastapi import HTTPException
from loguru import logger
from openai import AsyncOpenAI


async def create_test(project_id: str, org_id: str) -> Test:
    mongo_db = await get_mongo_db()
    creation_timestamp = generate_timestamp()
    try:
        test_data = Test(
            project_id=project_id,
            org_id=org_id,
            created_by=org_id,
            created_at=creation_timestamp,
            last_updated_at=creation_timestamp,
            status="started",
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to create test: {e}")
    await mongo_db["tests"].insert_one(test_data.model_dump())
    return test_data


async def get_test_by_id(test_id: str) -> Test:
    mongo_db = await get_mongo_db()
    test = await mongo_db["tests"].find_one({"id": test_id})
    if test is None:
        raise HTTPException(status_code=404, detail="Test not found")
    try:
        test = Test.model_validate(test)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to validate test: {e}")
    return test


async def compute_test_scores(test_id: str) -> float:
    """
    Compute the scores of a test when it is completed
    """
    mongo_db = await get_mongo_db()

    # Get the evaluations for the test
    evaluations = (
        await mongo_db["evals"].find({"test_id": test_id}).to_list(length=None)
    )

    eval_list = []

    for evaluation in evaluations:
        evaluation_data = evaluation.to_dict()
        evaluation_model = Eval.model_validate(evaluation_data)

        if evaluation_model.value == "success":
            eval_list.append(1)
        else:
            eval_list.append(0)

    # Get the comparisons for the test
    comparisons = (
        await mongo_db["comparisons"].find({"test_id": test_id}).to_list(length=None)
    )

    comparison_list: List[float] = []

    for comparison in comparisons:
        comparison_data = comparison.to_dict()
        comparison_model = Comparison.model_validate(comparison_data)

        # Extract the ComparisonResults
        comparison_result = comparison_model.comparison_result

        if comparison_result == "New output is better":
            comparison_list.append(1)
        elif comparison_result == "Old output is better":
            comparison_list.append(0)
        elif comparison_result == "Same quality" or comparison_result == "Both are bad":
            comparison_list.append(0.5)
        else:
            comparison_list.append(0)

    # Concate the two lists
    evaluations = eval_list + comparison_list

    logger.debug(
        f"Calculating test score with {len(eval_list)} evaluations and {len(comparison_list)} comparisons for test {test_id}"
    )

    # Get the mean score
    if len(evaluations) == 0:
        # TODO : how to handle this case ?
        overall_score = 0
    else:
        overall_score = sum(evaluations) / len(evaluations)

    return overall_score


async def update_test(
    test: Test,
    status: Optional[str] = None,
    summary: Optional[dict] = None,
) -> Test:
    test_summary = test.summary
    mongo_db = await get_mongo_db()

    # Parse the update payload
    update_payload: Dict[str, Any] = {}

    # Add the last_updated_at field
    timestamp = generate_timestamp()
    update_payload["last_updated_at"] = timestamp

    if status is not None:
        # The update request contains a status update
        update_payload["status"] = status

        # If the status is completed, compute the scores of the test
        if status == "completed":
            # Compute the scores of the test
            overall_score = await compute_test_scores(test.id)
            logger.info(f"Test {test.id} completed with overall score {overall_score}")

            # Save it in the database
            test_summary["overall_score"] = overall_score

        # Log the time elapsed if the test is completed
        if status == "completed" or status == "canceled":
            logger.info(
                f"Test {test.id} completed in {timestamp - test.created_at} seconds"
            )
            update_payload["terminated_at"] = timestamp

    if summary is not None:
        # For each key, update the test_summary object
        for key, value in summary.items():
            test_summary[key] = value

    update_payload["summary"] = test_summary

    logger.debug(f"Update payload: {update_payload} for test {test.id}")

    # Update the document if the payload is not empty
    if update_payload:
        update_result = await mongo_db["tests"].update_one(
            {"id": test.id}, {"$set": update_payload}
        )

    # Return the updated document
    updated_test = await get_test_by_id(test.id)
    return updated_test


async def compare_answers(
    context: str,
    old_output_str: str,
    new_output_str: str,
    project_id: str,
    instructions: Optional[str] = "",
    test_id: Optional[str] = None,
    org_id: Optional[str] = None,
) -> Comparison:
    """
    Compare the old and new answers to the context_input with an LLM
    TODO : move to a specific file, like we did for events
    """

    openai_client = openai_client = AsyncOpenAI(
        api_key=config.OPENAI_API_KEY,
    )

    if instructions is not None and instructions != "":
        additional_instructions = f"\nAdditional instructions: {instructions}\n"
    else:
        additional_instructions = ""

    prompt = f"""Chose which of the response is better as an answer to the context.{additional_instructions}
---
Context: {context}
---
Response A: {old_output_str}
---
Response B: {new_output_str}
----

Possible answers:
Choice A: Response A is better
Choice B: Response B is better
Choice C: Both are equally good
Choice D: Both are equally bad

Choice: """

    # TODO : Use response schema to coerce more the output generation
    response = await openai_client.chat.completions.create(
        messages=[{"role": "system", "content": prompt}],
        model="gpt-3.5-turbo",
        max_tokens=2,
    )
    text_response = response.choices[0].message.content
    # Map back 'Choice A' to 'Response A is better' etc.
    # TODO : Automate this extraction
    mapping = {
        "Choice A": "Old output is better",
        "A": "Old output is better",
        "A:": "Old output is better",
        "Choice B": "New output is better",
        "B": "New output is better",
        "B:": "New output is better",
        "Choice C": "Same quality",
        "C": "Same quality",
        "C:": "Same quality",
        "Choice D": "Both are bad",
        "D": "Both are bad",
        "D:": "Both are bad",
    }
    if text_response is not None:
        text_response = text_response.strip()
        comparison_result = mapping.get(text_response, "Error")
    else:
        comparison_result = "Error"

    if comparison_result == "Error":
        logger.warning(f"Error while comparing answers: {text_response}")

    comparison_result_model = cast(ComparisonResults, comparison_result)

    comparison_data = Comparison(
        project_id=project_id,
        test_id=test_id,
        instructions=instructions,
        context_input=context,
        old_output=old_output_str,
        new_output=new_output_str,
        source="phospho",
        comparison_result=comparison_result_model,
        org_id=org_id,
    )

    # Store the comparison in the database
    mongo_db = await get_mongo_db()
    mongo_db["comparisons"].insert_one(comparison_data.model_dump())

    return comparison_data
