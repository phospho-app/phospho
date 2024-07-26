from fastapi import APIRouter, Depends
from loguru import logger
from propelauth_fastapi import User

from app.api.platform.models import (
    OnboardingSurvey,
)
from app.security.authentification import (
    propelauth,
)
from app.services.mongo.projects import (
    store_onboarding_survey,
)

router = APIRouter(tags=["Onboarding"])


@router.post(
    "/onboarding/log-onboarding-survey",
    description="Logs the onboarding survey answers",
    response_model=dict,
)
async def suggest_events(
    survey: OnboardingSurvey,
    user: User = Depends(propelauth.require_user),
) -> dict:
    """
    Logs the onboarding survey answers
    """
    await store_onboarding_survey(user, survey.model_dump())
    return {"status": "ok"}
