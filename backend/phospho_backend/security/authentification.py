"""
Handle all authentification related tasks.

We now use Propelauth for authentification.
"""

from typing import Optional

from fastapi import Depends, HTTPException, Request
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer
from fastapi.security.utils import get_authorization_scheme_param
from loguru import logger
from propelauth_fastapi import User, init_auth

from phospho_backend.core import config
from phospho_backend.db.mongo import get_mongo_db

propelauth = init_auth(config.PROPELAUTH_URL, config.PROPELAUTH_API_KEY)


bearer = HTTPBearer()


def is_org_in_alpha(org: dict) -> bool:
    """
    Check if an organization is in the alpha program
    """
    org_metadata = org["org"].get("metadata", {})
    if not org_metadata:
        return False

    return org_metadata.get("is_in_alpha", False)


def authenticate_org_key(
    authorization: HTTPAuthorizationCredentials = Depends(bearer),
) -> dict:
    """
    API key authentification for orgs

    Parses the authorization header and checks if the API key is valid.
    """
    # Parse credentials
    api_key_token = authorization.credentials

    try:
        org = propelauth.validate_org_api_key(api_key_token)

    except Exception as e:
        logger.debug(f"Caught Exception: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

    logger.debug(
        f"API key authentification for org {org['org']['org_id']} ending in {api_key_token[-4:]}"
    )

    return org


def authenticate_org_key_in_alpha(
    authorization: HTTPAuthorizationCredentials = Depends(bearer),
) -> dict:
    """
    API key authentification for orgs
    Request will be denied if the org is not in the alpha program
    """
    # Parse credentials
    api_key_token = authorization.credentials

    try:
        org = propelauth.validate_org_api_key(api_key_token)

        if not is_org_in_alpha(org):
            raise HTTPException(
                status_code=403,
                detail="Organization not in the Alpha program. Request access at contact@phospho.ai",
            )

    except Exception as e:
        logger.debug(f"Caught Exception: {e}")
        raise HTTPException(status_code=401, detail="Invalid token")

    logger.debug(
        f"API key authentification for org {org['org']['org_id']} ending in {api_key_token[-4:]}"
    )

    return org


def authenticate_org_key_no_exception(request: Request) -> Optional[dict]:
    """
    API key authentification for orgs. Does NOT raise an exception if the token is invalid.
    """
    try:
        # Parse credentials
        authorization = request.headers.get("Authorization")
        scheme, credentials = get_authorization_scheme_param(authorization)
        if authorization is None or scheme.lower() != "bearer":
            return None
        org = propelauth.validate_org_api_key(credentials)
    except Exception as e:
        logger.debug(f"Caught Exception: {e}")
        return None

    logger.debug(
        f"API key authentification for org {org['org']['org_id']} ending in {credentials[-4:]}"
    )

    return org


async def verify_propelauth_org_owns_project_id(org: dict, project_id: str) -> None:
    """
    Fetch the project and check that the org is the owner of the project.
    Used as a workaround when you don't know the org_id.

    TODO : Add org_id to the documents to avoid this costy check.
    """
    org_id = org["org"].get("org_id")
    if not org_id:
        raise HTTPException(status_code=403, detail="Access denied")

    mongo_db = await get_mongo_db()
    project_data = await mongo_db["projects"].find_one({"id": project_id})
    if not project_data:
        raise HTTPException(
            status_code=404,
            detail=f"Project {project_id} not found",
        )
    org_id_of_project = project_data.get("org_id")

    # Check that the org is the owner of the project
    if org_id != org_id_of_project:
        logger.error(f"Org {org_id} is not the owner of the project {project_id}")
        raise HTTPException(
            status_code=403,
            detail=f"Org {org_id} is not the owner of the project {project_id}",
        )


async def verify_if_propelauth_user_can_access_project(
    user: User, project_id: str
) -> str:
    """Verify if a Propelauth user can access a project. If not, raise an HTTPException.

    Raises:
    - HTTPException 403: If the user can't access the project.
    - HTTPException 404: If the project doesn't exist.

    Returns: The org_id of the project.
    """

    mongo_db = await get_mongo_db()
    project_data = await mongo_db["projects"].find_one({"id": project_id})

    if not project_data:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    # AUTHORIZATION
    org_id = project_data.get("org_id", None)
    if not org_id:
        logger.error(f"Project {project_id} has no org_id. Access denied.")
        raise HTTPException(
            status_code=403,
            detail=f"Project {project_id} has no org_id. Access denied.",
        )
    try:
        _ = propelauth.require_org_member(user, org_id)
    except Exception as e:
        logger.error(
            f"Can't verify that {user} is a member of org {org_id} due to: {e}"
        )
        raise HTTPException(
            status_code=403,
            detail=f"Can't verify that {user} is a member of org {org_id} due to: {e}",
        )
    return org_id


def raise_error_if_not_in_pro_tier(org: dict) -> None:
    """Raise an HTTPException if the org is not in the pro tier."""
    if not config.ENVIRONMENT == "production":
        return
    org_id = org["org"].get("org_id")
    # Exempted orgs
    if org_id in config.EXEMPTED_ORG_IDS:
        return

    org_metadata = org.get("metadata") or {"plan": "hobby"}
    if org_metadata is None or org_metadata.get("plan") != "pro":
        raise HTTPException(
            status_code=403,
            detail="This feature is only available with a payment method. Add it on https://platform.phospho.ai/",
        )
    return
