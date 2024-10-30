from typing import Any, Dict, List

from app.api.platform.models.organizations import BillingStatsRequest
import stripe
from customerio import analytics  # type: ignore
from fastapi import APIRouter, BackgroundTasks, Depends, Header, HTTPException, Request
from loguru import logger
from propelauth_fastapi import User  # type: ignore

from app.api.platform.models import (
    CreateCheckoutRequest,
    CreateDefaultProjectRequest,
    Project,
    ProjectCreationRequest,
    Projects,
    UserCreatedEventWebhook,
)
from app.core import config
from app.security.authentification import propelauth
from app.services.mongo.emails import email_user_onboarding, send_payment_issue_email
from app.services.mongo.organizations import (
    change_organization_plan,
    create_project_by_org,
    daily_billing_stats,
    get_projects_from_org_id,
    get_usage_quota,
)
from app.services.mongo.projects import get_project_by_id, copy_template_project_to_new
from app.services.slack import slack_notification
from phospho.models import UsageQuota
from phospho.utils import generate_version_id

router = APIRouter(tags=["Organizations"])


@router.get(
    "/organizations/{org_id}/projects",
    response_model=Projects,
    description="Get all the projects of an organization",
)
async def get_org_projects(
    org_id: str, limit: int = 1000, user: User = Depends(propelauth.require_user)
) -> Projects:
    """
    Get the projects of an organization
    """
    logger.debug(f"Getting projects for org {org_id}")
    org_member_info = propelauth.require_org_member(user, org_id)
    projects = await get_projects_from_org_id(org_member_info.org_id, limit)
    return Projects(projects=projects)


@router.post(
    "/organizations/{org_id}/projects",
    response_model=Project,
    description="Create a new project",
)
async def post_create_project(
    org_id: str,
    project_request: ProjectCreationRequest,
    user: User = Depends(propelauth.require_user),
) -> Project:
    org_member_info = propelauth.require_org_member(user, org_id)
    project = await create_project_by_org(
        org_id=org_id, user_id=user.user_id, **project_request.model_dump()
    )
    # Send a notification if it's not a phospho project
    if (
        config.ENVIRONMENT == "production"
        and org_member_info.org_id != "e4M5ZDH2pwXz8ddEbVIR"
    ):  # TODO if not the phospho org
        # Get the user info
        logger.info(f"New project created : {project.project_name}")
        await slack_notification(
            f"Project {project.project_name} {project.id} created by user with"
            + f" id {user.email} in organization {org_member_info.org_name}"
        )

    return project


@router.post(
    "/organizations/{org_id}/create-default-project",
    response_model=Project,
    description="Create a new default project",
)
async def post_create_default_project(
    org_id: str,
    request: CreateDefaultProjectRequest,
    user: User = Depends(propelauth.require_user),
) -> Project:
    org_member_info = propelauth.require_org_member(user, org_id)
    template_name = request.template_name

    # The project will be created with a specific name
    template_to_project_name = {
        "history": "The History I forgot",
        "animals": "Rude Biology teacher",
        "medical": "The Worst Doctor",
    }

    if request.project_id:
        project = await get_project_by_id(request.project_id)
    else:
        project = await create_project_by_org(
            org_id=org_id,
            user_id=user.user_id,
            project_name=template_to_project_name.get(template_name, "Default Project"),
        )
    logger.debug(f"Creating default project for org {org_id}")
    logger.debug(f"Target project id: {template_name}")
    await copy_template_project_to_new(
        project_id=project.id, org_id=org_id, template_name=template_name
    )
    # Send a notification if it's not a phospho project
    if (
        config.ENVIRONMENT == "production"
        and org_member_info.org_id != "e4M5ZDH2pwXz8ddEbVIR"
    ):
        # Get the user info
        logger.info(f"New default project created : {project.project_name}")
        await slack_notification(
            f"Default project {project.project_name} {project.id} created by user with"
            + f" id {user.email} in organization {org_member_info.org_name}"
        )
    return project


@router.post(
    "/organizations/{org_id}/init",
    description="Ininitialize an organization",
)
async def post_init_org(
    org_id: str,
    background_tasks: BackgroundTasks,
    user: User = Depends(propelauth.require_user),
) -> dict:
    # Auth
    try:
        propelauth.require_org_member(user, org_id)
    except Exception as e:
        logger.error(f"Error initializing organization {org_id} : {e}")
        return {
            "status": "error",
            "detail": str(e),
        }

    output: Dict[str, Any] = {}

    # Next page to redirect to
    output["redirect_url"] = "/org/transcripts/sessions"
    # Check if org has at least 1 project
    org_projects = await get_projects_from_org_id(org_id, limit=1)
    if len(org_projects) == 0:
        # Create a default project
        logger.debug(f"Creating default project for org {org_id}")
        selected_project = await create_project_by_org(
            org_id=org_id,
            user_id=user.user_id,
            project_name=generate_version_id(with_date=False),
        )
        output["redirect_url"] = "/onboarding"
    else:
        # The org already has a project
        selected_project = org_projects[0]
    output["selected_project"] = selected_project

    # Get the org metatdata to check if it's already initialized
    try:
        org = propelauth.fetch_org(org_id)
    except Exception as e:
        logger.error(f"Propelauth error fetching organization {org_id}: {e}")
        return {
            **output,
            "status": "error",
            "detail": f"Error fetching organization: {e}",
        }

    # Get the org metadata
    org_metadata = org.get("metadata", {})

    # Check if the metadata is initialized
    if org_metadata.get("initialized", False):
        logger.debug(f"Organization {org_id} already initialized")
        return {
            **output,
            "status": "ok",
            "detail": "Organization already initialized",
        }

    # Organization not initialized. Redirect to onboarding
    output["redirect_url"] = "/onboarding"

    # Alternative for historical users: check if the plan is already set
    if org_metadata.get("plan", None) is not None:
        # Org already initialized
        logger.debug(f"Organization {org_id} already initialized")

        # Set the initialized flag
        org_metadata["initialized"] = True
        propelauth.update_org_metadata(org_id, metadata=org_metadata)
        if org_metadata.get("plan", "hobby") == "pro":
            propelauth.update_org_metadata(org_id, max_users=config.PLAN_PRO_MAX_USERS)
        elif org_metadata.get("plan", "hobby") == "hobby":
            propelauth.update_org_metadata(
                org_id, max_users=config.PLAN_HOBBY_MAX_USERS
            )
        return {
            **output,
            "status": "ok",
            "detail": "Organization already has a plan set, no need to initialize it",
        }

    try:
        # Check if we are in self-hosted mode
        if config.ENVIRONMENT == "preview":
            propelauth.update_org_metadata(
                org_id,
                max_users=config.PLAN_SELFHOSTED_MAX_USERS,
                metadata={"plan": "self-hosted", "initialized": True},
            )
            logger.info(
                f"Organization {org_id} initialized with max_users={config.PLAN_SELFHOSTED_MAX_USERS} and plan=self-hosted"
            )
            return {**output, "status": "ok", "selected_project": selected_project}

        # Otherwise, we are in the cloud mode
        # Initialize the organization with the hobby plan
        propelauth.update_org_metadata(
            org_id,
            max_users=config.PLAN_HOBBY_MAX_USERS,
            metadata={"plan": "hobby", "initialized": True},
        )
        logger.info(
            f"Organization {org_id} initialized with max_users={config.PLAN_HOBBY_MAX_USERS} and plan=hobby"
        )

        # Send the welcome email as a background task
        user_email = user.email
        if user_email:
            # Trigger the email in the background
            background_tasks.add_task(email_user_onboarding, email=user_email)
        else:
            logger.error(f"User {user.user_id} has no email")
            return {
                **output,
                "status": "error",
                "detail": "User has no email",
            }

        return {**output, "status": "ok"}
    except Exception as e:
        logger.error(f"Error initializing organization {org_id} : {e}")
        return {
            **output,
            "status": "error",
            "detail": str(e),
        }


@router.get(
    "/organizations/{org_id}/usage-quota",
    description="Get the usage quota of an organization",
    response_model=UsageQuota,
)
async def get_org_usage_quota(
    org_id: str,
    user: User = Depends(propelauth.require_user),
) -> UsageQuota:
    _ = propelauth.require_org_member(user, org_id)
    org = propelauth.fetch_org(org_id)
    logger.info(org)
    org_metadata = org.get("metadata", {})
    org_plan = org_metadata.get("plan", "hobby")
    customer_id = org_metadata.get("customer_id", None)
    usage_quota = await get_usage_quota(org_id, plan=org_plan, customer_id=customer_id)

    return usage_quota


@router.get(
    "/organizations/{org_id}/metadata",
    description="Get the metadata of an organization",
)
async def get_org_metadata(
    org_id: str,
    user: User = Depends(propelauth.require_user),
):
    org = propelauth.require_org_member(user, org_id)
    org = propelauth.fetch_org(org_id)
    org_metadata = org.get("metadata", {"plan": "hobby"})
    org_metadata.update({"org_id": org_id})
    return org_metadata


@router.post(
    "/organizations/{org_id}/create-checkout",
    description="Create a stripe checkout session for an organization",
)
async def post_create_checkout_session(
    org_id: str,
    create_checkout_request: CreateCheckoutRequest,
    user: User = Depends(propelauth.require_user),
):
    _ = propelauth.require_org_member(user, org_id)
    org = propelauth.fetch_org(org_id)
    org_metadata = org.get("metadata", {})
    org_plan = org_metadata.get("plan", "hobby")

    if org_plan == "pro":
        # Organization already has a pro plan
        return {"error": "Organization already has a pro plan"}

    if org_plan == "self-hosted":
        # Organization already has a self-hosted plan
        logger.error(
            f"Organization {org_id} is in a self-hosted plan but requested a pro plan"
        )
        return {"error": "Organization is in a self-hosted plan"}
    # Create the checkout session
    stripe.api_key = config.STRIPE_SECRET_KEY
    try:
        logger.debug(
            f"Creating checkout session for org {org_id} and user {user.email}"
        )

        success_url = f"{config.PHOSPHO_FRONTEND_URL}/checkout/thank-you"
        if create_checkout_request.project_id:
            success_url += f"?project_id={create_checkout_request.project_id}"

        checkout_session = stripe.checkout.Session.create(
            line_items=[
                {
                    # This is the Stripe price ID for the pro plan subscription
                    # https://dashboard.stripe.com/products?active=true
                    "price": config.PRO_PLAN_STRIPE_PRICE_ID,
                },
            ],
            mode="subscription",
            success_url=success_url,
            cancel_url=f"{config.PHOSPHO_FRONTEND_URL}/checkout/cancel",
            customer_email=user.email,
            metadata={"org_id": org_id},
            subscription_data={
                "trial_settings": {
                    "end_behavior": {"missing_payment_method": "cancel"}
                },
                "description": "Unlock phospho's full potential.",
            },
            allow_promotion_codes=True,
        )
    except Exception as e:
        return {"error": f"Unexpected error: {e}"}

    if checkout_session.url is None:
        return {"error": "Error creating checkout session"}

    return {"checkout_url": checkout_session.url}


@router.post(
    "/organizations/stripe-webhook",
    description="Stripe webhook to handle events",
)
async def post_stripe_webhook(
    request: Request,
    background_tasks: BackgroundTasks,
    stripe_signature: str = Header(None),
):
    payload = await request.body()
    stripe.api_key = config.STRIPE_SECRET_KEY

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=stripe_signature,
            secret=config.STRIPE_WEBHOOK_SECRET,
        )
    except ValueError as e:
        # Invalid payload
        logger.debug(f"Invalid payload: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid payload: {e}")
    except stripe.StripeError as e:
        # Invalid signature
        logger.debug(f"Stripe error: {e}")
        raise HTTPException(status_code=400, detail=f"Invalid signature: {e}")
    except Exception as e:
        # Unexpected error
        logger.debug(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Unexpected error: {e}")

    logger.info(f"Received stripe event {event['type']}")

    if event["type"] == "checkout.session.completed":
        # Retrieve the session. If you require line items in the response,
        # you may include them by expanding line_items.
        session = stripe.checkout.Session.retrieve(
            event["data"]["object"]["id"],
            expand=["line_items"],
        )
        line_items = session.line_items
        if line_items is None:
            return {"status": "ok"}
        for item in line_items:
            price = item.get("price", None)
            product = price.get("product", None)
            customer_id = session.get("customer", None)
            if product == config.PRO_PLAN_STRIPE_PRODUCT_ID and customer_id is not None:
                # This is the pro plan subscription
                # Get the org_id from the metadata
                org_id = session.get("metadata", {}).get("org_id", None)
                if org_id is None:
                    # Send an email to the user
                    logger.error(
                        f"No org_id in metadata for stripe checkout session {session.id}"
                    )
                    if session.customer_email:
                        background_tasks.add_task(
                            send_payment_issue_email, to_email=session.customer_email
                        )
                    else:
                        await slack_notification(
                            f"/!\ Automatic activation failed! Stripe checkout session {session.id}"
                            + " was processed but has no org_id in metadata and no customer email"
                        )
                else:
                    # Activate the organization
                    logger.info(f"Activating organization {org_id} with plan pro")

                    background_tasks.add_task(
                        change_organization_plan,
                        org_id=org_id,
                        plan="usage_based",
                        customer_id=customer_id,
                    )
            else:
                # We don't know this !
                logger.error(
                    f"Unknown line item in stripe checkout\nsession: {session}\nitem: {item}"
                )
                await slack_notification(
                    f"Unknown line item in stripe checkout\nsession: {session}\nitem: {item}"
                )

    # TODO: handle other events
    # https://docs.stripe.com/api/events/types
    # For example, to handle a subscription update, payment error, or a checkout cancelation

    if event["type"].startswith("customer.subscription"):
        # https://docs.stripe.com/api/subscriptions/object
        subscription = stripe.Subscription.retrieve(
            event["data"]["object"]["id"], expand=["items.data", "customer"]
        )
        logger.debug(f"Subscription {subscription.id} retrieved: {subscription}")
        # Org id is in the customer metadata
        org_id = (
            subscription.get("customer", {}).get("metadata", {}).get("org_id", None)
        )
        customer_id = subscription.get("customer", {}).get("id", None)
        # This corresponds to legacy subscriptions
        if event["type"] == "customer.subscription.trial_will_end":
            logger.warning("Unhandled: Subscription trial will end")
            return {"status": "ok"}
        if event["type"] in [
            "customer.subscription.updated",
        ]:
            logger.info(f"Subscription {subscription.id} updated")
            # Get the new plan
            plan = subscription.get("plan", {})
            plan_active = plan.get("active", False)
            plan_product = plan.get("product", None)
            if plan_product == config.PRO_PLAN_STRIPE_PRODUCT_ID and plan_active:
                # This is the pro plan subscription
                if org_id is not None:
                    # Upgrade the organization to the pro plan
                    logger.info(f"Upgrading organization {org_id} to pro plan")
                    background_tasks.add_task(
                        change_organization_plan,
                        org_id=org_id,
                        plan="usage_based",
                        customer_id=customer_id,
                    )
                else:
                    logger.error(
                        f"No org_id in metadata for stripe subscription {subscription.id}"
                    )
                    await slack_notification(
                        f"/!\ Automatic upgrade failed! Stripe subscription {subscription.id}"
                        + " was updated but has no org_id in metadata"
                    )
            elif plan_product == config.PRO_PLAN_STRIPE_PRODUCT_ID and not plan_active:
                # This is the pro plan subscription
                if org_id is not None:
                    # Downgrade the organization to the hobby plan
                    logger.info(f"Downgrading organization {org_id} to plan hobby")
                    background_tasks.add_task(
                        change_organization_plan,
                        org_id=org_id,
                        plan="hobby",
                        customer_id=None,
                    )
                else:
                    logger.error(
                        f"No org_id in metadata for stripe subscription {subscription.id}"
                    )
                    await slack_notification(
                        f"/!\ Automatic downgrade failed! Stripe subscription {subscription.id}"
                        + " was updated but has no org_id in metadata"
                    )

        if event["type"] in [
            "customer.subscription.canceled",
            "customer.subscription.deleted",
        ]:
            if org_id is not None:
                # Downgrade the organization to the hobby plan
                logger.info(f"Downgrading organization {org_id} to plan hobby")
                background_tasks.add_task(
                    change_organization_plan,
                    org_id=org_id,
                    plan="hobby",
                    customer_id=customer_id,
                )
            else:
                logger.error(
                    f"No org_id in metadata for stripe subscription {subscription.id}"
                )
                await slack_notification(
                    f"/!\ Automatic downgrade failed! Stripe subscription {subscription.id}"
                    + " was updated but has no org_id in metadata"
                )

    # Passed signature verification
    return {"status": "ok"}


@router.post(
    "/organizations/{org_id}/billing-portal",
    description="Create a stripe billing portal session for an organization",
)
async def post_create_billing_portal_session(
    org_id: str,
    user: User = Depends(propelauth.require_user),
):
    _ = propelauth.require_org_member(user, org_id)
    org = propelauth.fetch_org(org_id)
    org_metadata = org.get("metadata", {})
    org_plan = org_metadata.get("plan", "hobby")
    if org_plan == "hobby":
        return {"error": "Organization has a hobby plan, no billing portal available"}

    if org_plan == "self-hosted":
        logger.error(
            f"Organization {org_id} is in a self-hosted plan but requested a billing portal"
        )
        return {
            "error": "Organization has a self-hosted plan, no billing portal available"
        }
    if org_id in config.EXEMPTED_ORG_IDS:
        return {"error": "Organization is exempted from billing portal"}
    stripe.api_key = config.STRIPE_SECRET_KEY
    try:
        logger.debug(
            f"Creating billing portal session for org {org_id}, user {user.email}, and customer {org_metadata.get('customer_id', None)}"
        )
        # Update the metadata of the customer in stripe
        stripe.Customer.modify(
            org_metadata.get("customer_id", None),
            metadata={"org_id": org_id},
        )
        portal_session = stripe.billing_portal.Session.create(
            customer=org_metadata.get("customer_id", None),
            return_url=f"{config.PHOSPHO_FRONTEND_URL}/org/settings/billing",
        )
        return {"portal_url": portal_session.url}
    except Exception as e:
        logger.error(f"Error creating billing portal session: {e}")
        return {"error": f"Unexpected error: {e}"}


@router.post(
    "/organizations/propelauth-webhook",
    description="Propelauth webhook to handle events",
)
async def post_propelauth_webhook(
    event: UserCreatedEventWebhook,
):
    """
    Used for keeping track of created users in the platform
    and syncing emails.
    """
    analytics.write_key = config.CUSTOMERIO_WRITE_KEY
    analytics.endpoint = "https://cdp-eu.customer.io"  # EU endpoint

    if event.event_type == "user.created":
        # Sync the user with customer.io
        analytics.identify(
            event.user_id,
            {
                "email": event.email,
                "first_name": event.first_name,
                "last_name": event.last_name,
            },
        )
    return {"status": "ok"}


@router.get(
    "/organizations/{org_id}/nb-users-and-plan",
    description="Get the number of users in an organization",
)
async def get_org_number_users(
    org_id: str,
    user: User = Depends(propelauth.require_user),
):
    propelauth.require_org_member(user, org_id)
    org = propelauth.fetch_users_in_org(org_id)
    total_users = org.get("totalUsers", 0)
    org_metadata = org.get("metadata", {})
    org_plan = org_metadata.get("plan", "hobby")
    return {"total_users": total_users, "plan": org_plan}


@router.post(
    "/organizations/{org_id}/billing-stats",
    description="Get the billing stats for the organization (daily usage)",
)
async def post_billing_stats(
    org_id: str,
    query: BillingStatsRequest,
    user: User = Depends(propelauth.require_user),
) -> List[dict]:
    propelauth.require_org_member(user, org_id)
    return await daily_billing_stats(
        org_id=org_id,
        usage_type=query.usage_type,
    )
