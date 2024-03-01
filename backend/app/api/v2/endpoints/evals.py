from fastapi import APIRouter, Depends

from app.api.v2.models import Comparison, ComparisonQuery
from app.security import authenticate_org_key, verify_propelauth_org_owns_project_id
from app.services.mongo.tests import compare_answers

router = APIRouter(tags=["evals"])


@router.post(
    "/evals/compare",
    response_model=Comparison,
    description="Compare the old and new answers to the context_input",
)
async def post_compare_answers(
    query: ComparisonQuery,
    org: dict = Depends(authenticate_org_key),
) -> Comparison:
    """
    Compare the old and new answers to the context_input.
    """

    await verify_propelauth_org_owns_project_id(org, query.project_id)
    comparison_data = await compare_answers(
        context=query.context_input,
        old_output_str=query.old_output,
        new_output_str=query.new_output,
        instructions=query.instructions,
        project_id=query.project_id,
        test_id=query.test_id,
        org_id=org["org"].get("org_id"),
    )

    return comparison_data
