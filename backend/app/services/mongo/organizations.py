from typing import List, Optional

import pydantic
from fastapi import HTTPException
from loguru import logger

from app.db.models import Project
from app.db.mongo import get_mongo_db
from app.core import config
from app.security.authentification import propelauth


async def get_projects_from_org_id(org_id: str, limit: int = 1000) -> List[Project]:
    # Get the projects of the organization, ordered by creation date
    mongo_db = await get_mongo_db()
    project_list = (
        await mongo_db["projects"]
        .find({"org_id": org_id})
        .sort("created_at", -1)
        .limit(limit)
        .to_list(length=limit)
    )
    # Convert to a list of Project objects
    projects = [Project(**project) for project in project_list]
    return projects


async def create_project_by_org(org_id: str, user_id: str, **kwargs) -> Project:
    if "settings" in kwargs:
        if kwargs["settings"] is None:
            # Let the default field creator be used
            kwargs.pop("settings")

    try:
        project = Project(
            org_id=org_id,
            user_id=user_id,
            **kwargs,
        )
    except pydantic.ValidationError as e:
        logger.warning(f"Error validating project model for org {org_id}")
        raise HTTPException(
            status_code=400, detail=f"Error while creating project: {e}"
        )
    mongo_db = await get_mongo_db()
    result = await mongo_db["projects"].insert_one(project.model_dump())
    return project


async def get_usage_quota(org_id: str, plan: str) -> dict:
    """
    Calculate the usage quota of an organization.
    The usage quota is the number of tasks logged by the organization.
    """
    mongo_db = await get_mongo_db()
    nb_tasks_logged = await mongo_db["tasks"].count_documents({"org_id": org_id})
    if plan == "hobby":
        max_usage = config.PLAN_HOBBY_MAX_NB_TASKS
        max_usage_label = str(config.PLAN_HOBBY_MAX_NB_TASKS)
    elif plan == "pro":
        max_usage = None
        max_usage_label = "unlimited"
    return {
        "org_id": org_id,
        "plan": plan,
        "current_usage": nb_tasks_logged,
        "max_usage": max_usage,
        "max_usage_label": max_usage_label,
    }


def fetch_users_from_org(org_id: str):
    """
    Get all the users of an organization
    Returns a list of users in the propelAuth format
    See : https://docs.propelauth.com/reference/api/org#fetch-users-in-org
    """
    first_user_response = propelauth.fetch_users_in_org(
        org_id=org_id, page_size=99, page_number=0
    )

    # Get the number of users
    number_of_users = first_user_response.get("total_users")

    users = first_user_response.get("users")

    if number_of_users > 99:  # max nb of users on 1 page
        # Get all the users
        for page_number in range(1, number_of_users // 99 + 1):
            users += propelauth.fetch_users_in_org(
                org_id=org_id,
                page_size=99,
                page_number=page_number,
            ).users

    return users


def change_organization_plan(
    org_id: str, plan: str = "pro", customer_id: Optional[str] = None
) -> Optional[dict]:
    """
    Upgrade the organization to the pro plan
    """
    try:
        # Upgrade the organization to the pro plan
        org = propelauth.fetch_org(org_id)
        org_metadata = org.get("metadata", {})
        # Set the plan to pro
        org_metadata["plan"] = plan
        # Set the customer_id
        org_metadata["customer_id"] = customer_id
        propelauth.update_org_metadata(
            org_id, max_users=config.PLAN_PRO_MAX_USERS, metadata=org_metadata
        )
        return org_metadata
    except Exception as e:
        logger.error(f"Error upgrading organization {org_id} to pro plan: {e}")
        return None
