import datetime
from typing import List, Literal, Optional

import pandas as pd
import pydantic
import stripe
from app.core import config
from app.db.models import Project
from app.db.mongo import get_mongo_db
from app.security.authentification import propelauth
from fastapi import HTTPException
from loguru import logger

from phospho.models import Recipe, UsageQuota


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
    # Add event_name if not present
    projects = []
    for project_data in project_list:
        try:
            project = Project.from_previous(project_data)
            for event_name, event in project.settings.events.items():
                if not event.recipe_id:
                    recipe = Recipe(
                        org_id=project.org_id,
                        project_id=project.id,
                        recipe_type="event_detection",
                        parameters=event.model_dump(),
                    )
                    mongo_db["recipes"].insert_one(recipe.model_dump())
                    project.settings.events[event_name].recipe_id = recipe.id
            if project.model_dump() != project_data:
                mongo_db["projects"].update_one(
                    {"_id": project_data["_id"]}, {"$set": project.model_dump()}
                )
            projects.append(project)
        except Exception as e:
            logger.warning(
                f"Error validating model of project {project_data.get('id')}: {e}"
            )

    return projects


async def create_project_by_org(
    org_id: str, user_id: Optional[str], **kwargs
) -> Project:
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

    # If the project name already exists for this org, add a suffix
    project_name = project.project_name
    suffix = 1
    while (
        await mongo_db["projects"].count_documents(
            {"org_id": org_id, "project_name": project_name}
        )
        > 0
    ) and suffix < 100:
        project_name = f"{project.project_name} ({suffix})"
        suffix += 1

    project.project_name = project_name

    # If some events are created, first let's create the coresponding Jobs objects
    # Let's get the events in the settings
    if project.settings.events:
        for event_name, event in project.settings.events.items():
            recipe = Recipe(
                org_id=org_id,
                project_id=project.id,
                recipe_type="event_detection",
                parameters=event.model_dump(),
            )
            mongo_db["recipes"].insert_one(recipe.model_dump())
            # Update the settings with the job_id
            project.settings.events[event_name].recipe_id = recipe.id

    await mongo_db["projects"].insert_one(project.model_dump())

    return project


async def get_usage_quota(
    org_id: str,
    plan: str,
    customer_id: Optional[str] = None,
    fetch_invoice: bool = True,
) -> UsageQuota:
    """
    Calculate the usage quota of an organization.
    The usage quota is the number of tasks logged by the organization.
    """
    mongo_db = await get_mongo_db()

    # Get usage info for the orgnization
    nb_tasks_logged = await mongo_db["job_results"].count_documents({"org_id": org_id})

    # Default config (plan == "hobby")
    max_usage: Optional[int] = config.PLAN_HOBBY_MAX_NB_DETECTIONS
    max_usage_label = str(config.PLAN_HOBBY_MAX_NB_DETECTIONS)

    if plan == "usage_based":
        max_usage = None
        max_usage_label = "unlimited"

    if plan == "pro" or org_id in config.EXEMPTED_ORG_IDS:
        max_usage = None
        max_usage_label = "unlimited"

    if plan == "self-hosted":
        max_usage = None
        max_usage_label = "unlimited"

    # Return the balance transaction if the org has a stripe customer id
    balance_transaction = None
    next_invoice_total = None
    next_invoice_amount_due = None

    if fetch_invoice:
        try:
            if customer_id is not None and config.ENVIRONMENT != "test":
                stripe.api_key = config.STRIPE_SECRET_KEY
                # Display free credits
                response = stripe.Customer.list_balance_transactions(
                    customer_id,
                    limit=1,
                )
                data = response.get("data", [])
                if data:
                    balance_transaction = data[0].get("amount", 0)

                # Display next invoice
                invoice_preview = stripe.Invoice.create_preview(customer=customer_id)
                next_invoice_total = invoice_preview.get("total", 0)

                # todo : use amount_due instead of total
                next_invoice_amount_due = invoice_preview.get("amount_due", 0)
        except Exception as e:
            logger.warning(f"Error fetching stripe data for org {org_id}: {e}")

    return UsageQuota(
        org_id=org_id,
        plan=plan,
        current_usage=nb_tasks_logged,
        max_usage=max_usage,
        max_usage_label=max_usage_label,
        balance_transaction=balance_transaction,
        next_invoice_total=next_invoice_total,
        next_invoice_amount_due=next_invoice_amount_due,
        customer_id=customer_id,
    )


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
    org_id: str, plan: str = "usage_based", customer_id: Optional[str] = None
) -> Optional[dict]:
    """
    Upgrade the organization to a usage_based plan
    """
    if config.ENVIRONMENT == "preview":
        logger.error("Cannot upgrade organization in preview environment")
        return None
    try:
        # Upgrade the organization to the pro plan
        org = propelauth.fetch_org(org_id)
        org_metadata = org.get("metadata", {})
        old_plan = org_metadata.get("plan", "hobby")
        # Set the plan to pro
        org_metadata["plan"] = plan
        # Set the customer_id
        org_metadata["customer_id"] = customer_id
        propelauth.update_org_metadata(
            org_id, max_users=config.PLAN_PRO_MAX_USERS, metadata=org_metadata
        )
        stripe.api_key = config.STRIPE_SECRET_KEY

        # Update the customer metadata with the org_id

        stripe.Customer.modify(
            org_metadata.get("customer_id", None),
            metadata={"org_id": org_id},
        )

        if plan == "usage_based" and old_plan == "hobby" and customer_id:
            # Attribute free credits to the organization
            stripe.Customer.create_balance_transaction(
                customer_id,
                amount=-1000,  # in cents
                currency="usd",
                description="[auto] Free credits for new organization",
            )

        return org_metadata
    except Exception as e:
        logger.error(f"Error upgrading organization {org_id} to pro plan: {e}")
        return None


async def daily_billing_stats(
    org_id: str,
    usage_type: Literal[
        "event_detection",
        "clustering",
        "sentiment",
        "language",
    ],
) -> List[dict]:
    """
    Query the job_results table and returns billing stats
    """

    pipeline = []
    mongo_db = await get_mongo_db()
    last_30days_ts = (datetime.datetime.now() - datetime.timedelta(days=30)).timestamp()

    set_date = {
        "$set": {
            "date": {
                "$dateToString": {
                    "format": "%Y-%m-%d",
                    "date": {"$toDate": {"$multiply": ["$created_at", 1000]}},
                }
            }
        }
    }

    if usage_type == "sentiment" or usage_type == "language":
        pipeline = [
            {
                "$match": {
                    "org_id": org_id,
                    "job_id": usage_type,
                    "created_at": {"$gte": last_30days_ts},
                }
            },
            set_date,
            {
                "$group": {
                    "_id": "$date",
                    "usage": {"$sum": 1},
                }
            },
            {"$project": {"_id": 0, "date": "$_id", "usage": 1}},
        ]
    elif usage_type == "clustering":
        pipeline = [
            {
                "$match": {
                    "org_id": org_id,
                    "job_id": "generate_clustering",
                    "created_at": {"$gte": last_30days_ts},
                }
            },
            set_date,
            {
                "$group": {
                    "_id": "$date",
                    "usage": {"$sum": "$value.nb_credits_used"},
                }
            },
            {"$project": {"_id": 0, "date": "$_id", "usage": 1}},
        ]

    elif usage_type == "event_detection":
        pipeline = [
            {
                "$match": {
                    "org_id": org_id,
                    "created_at": {"$gte": last_30days_ts},
                    "job_metadata.recipe_type": "event_detection",
                }
            },
            set_date,
            {
                "$group": {
                    "_id": "$date",
                    "usage": {"$sum": 1},
                }
            },
            {"$project": {"_id": 0, "date": "$_id", "usage": 1}},
        ]
    else:
        raise NotImplementedError(f"Usage type {usage_type} not implemented")

    logger.info(f"Running pipeline : {pipeline}")

    result = await mongo_db["job_results"].aggregate(pipeline).to_list(length=None)
    logger.info(f"Result for {usage_type} billing stats: {result}")

    # Fill the missing days
    min_date = datetime.datetime.now() - datetime.timedelta(days=30)
    max_date = datetime.datetime.now()
    date_range = pd.date_range(min_date, max_date)
    df_results = pd.DataFrame(result)
    df_date = pd.DataFrame({"date": date_range.strftime("%Y-%m-%d")})
    df = pd.merge(df_date, df_results, on="date", how="left")

    return df.to_dict(orient="records")
