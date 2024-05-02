import time
import stripe
from app.core import config

from phospho.models import UsageQuota
from loguru import logger
from app.db.mongo import get_mongo_db


async def increase_usage_for_org(org_id: str, nb_events_to_log: int) -> None:
    """
    Increase the usage of an organization.
    """
    current_timestamp = time.time()
    mongo_db = await get_mongo_db()

    usage = UsageQuota(
        credits_used=nb_events_to_log,
        org_id=org_id,
    )

    document = await mongo_db["usage"].find_one(
        {
            "org_id": org_id,
            "period_start": {"$lte": current_timestamp},
            "period_end": {"$gte": current_timestamp},
        }
    )

    if document:
        result = await mongo_db["usage"].update_one(
            {
                "org_id": org_id,
                "period_start": {"$lte": current_timestamp},
                "period_end": {"$gte": current_timestamp},
            },
            {
                "$inc": {"credits_used": nb_events_to_log},
                "$set": {"credits_consumed_since_last_reported": True},
            },
        )
    else:
        await mongo_db["usage"].insert_one(usage.model_dump())

    logger.debug(f"Usage update result: {result}")
    logger.info(f"Org {org_id} has spent {nb_events_to_log} credits ")

    return None


async def bill_on_stripe(
    org_id: str,
    nb_events_to_bill: int,
) -> None:
    """
    Bill an organization on Stripe
    """

    stripe.api_key = config.STRIPE_SECRET_KEY

    # Get the stripe customer id from usage table
    mongo_db = await get_mongo_db()
    usage = await mongo_db["usage"].find_one({"org_id": org_id})
    customer_id = usage.get("stripe_customer_id", None)

    if customer_id:
        stripe.billing.MeterEvent.create(
            event_name="phospho_usage_based_meter",
            payload={
                "value": nb_events_to_bill,
                "stripe_customer_id": customer_id,
            },
        )

    else:
        # We check if the org_id is on the usage_based plan
        org = await mongo_db["organizations"].find_one({"_id": org_id})
        if org.get("plan", None) == "usage_based":
            logger.error(
                f"Org {org_id} should have a stripe customer id but it doesn't, fix ASAP"
            )

    return None
