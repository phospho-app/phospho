from fastapi import APIRouter, Depends

from app.api.v2.models import Test, TestCreationRequest, TestUpdateRequest
from app.security import authenticate_org_key, verify_propelauth_org_owns_project_id
from app.services.mongo.tests import (
    create_test,
    get_test_by_id,
    update_test,
)

router = APIRouter(tags=["Tests"])


@router.post(
    "/tests",
    response_model=Test,
    description="Create a new test for a project",
)
async def post_create_test(
    testCreationRequest: TestCreationRequest,
    org: dict = Depends(authenticate_org_key),
) -> Test:
    project_id = testCreationRequest.project_id
    await verify_propelauth_org_owns_project_id(org, project_id)
    org_id = org["org"].get("org_id")
    test_data = await create_test(project_id=project_id, org_id=org_id)
    return test_data


@router.post(
    "/tests/{test_id}",
    response_model=Test,
    description="Update a test",
)
async def post_update_test(
    test_id: str,
    testUpdateRequest: TestUpdateRequest,
    org: dict = Depends(authenticate_org_key),
) -> Test:
    test = await get_test_by_id(test_id)
    await verify_propelauth_org_owns_project_id(org, test.project_id)
    return await update_test(test=test, **testUpdateRequest.model_dump())


@router.get(
    "/tests/{test_id}",
    response_model=Test,
    description="Get a test by its id",
)
async def get_test(
    test_id: str,
    org: dict = Depends(authenticate_org_key),
) -> Test:
    test = await get_test_by_id(test_id)
    await verify_propelauth_org_owns_project_id(org, test.project_id)
    return test
