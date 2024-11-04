from app.services.mongo.projects import project_check_automatic_analytics_monthly_limit
from app.services.mongo.recipes import run_recipe_types_on_tasks
from app.services.mongo.tasks import get_total_nb_of_tasks
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from propelauth_fastapi import User  # type: ignore

from app.api.platform.models import RunRecipeRequest
from app.security.authentification import (
    propelauth,
    verify_if_propelauth_user_can_access_project,
)
from app.core import config
from loguru import logger

router = APIRouter(tags=["Recipes"])


@router.post(
    "/recipes/{project_id}/run",
    response_model=dict,
    description="Run multiple recipes on tasks of a project",
)
async def post_run_recipes(
    project_id: str,
    run_recipe_request: RunRecipeRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(propelauth.require_user),
) -> dict:
    """
    Run multiple recipes of different types on tasks of a project
    """
    org_id = await verify_if_propelauth_user_can_access_project(user, project_id)
    org = propelauth.fetch_org(org_id)
    org_metadata = org.get("metadata", {})
    customer_id = None

    if "customer_id" in org_metadata.keys():
        customer_id = org_metadata.get("customer_id", None)

    if (
        not customer_id
        and org_id != config.PHOSPHO_ORG_ID
        and config.ENVIRONMENT in ["production", "staging"]
    ):
        raise HTTPException(
            status_code=402,
            detail="You need to add a payment method to access this service. Please update your payment details: https://platform.phospho.ai/org/settings/billing",
        )

    nb_tasks = await get_total_nb_of_tasks(
        project_id=project_id, filters=run_recipe_request.filters
    )

    is_over_limit = await project_check_automatic_analytics_monthly_limit(
        project_id=project_id,
        nb_tasks_to_process=nb_tasks,
        recipe_type_list=run_recipe_request.recipe_type_list,  # type: ignore
    )
    if is_over_limit:
        raise HTTPException(
            status_code=402,
            detail="You have reached the monthly limit of automatic analytics. Please increase your limit.",
        )

    logger.debug(
        f"Runinng following recipes on project {project_id}: {run_recipe_request.recipe_type_list}"
    )

    background_tasks.add_task(
        run_recipe_types_on_tasks,
        org_id=org_id,
        project_id=project_id,
        recipe_types=run_recipe_request.recipe_type_list,
        filters=run_recipe_request.filters,
    )
    return {"status": "ok"}
