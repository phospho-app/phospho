"""
Handle all authentification related tasks.

For now, we only use a single API key for the whole app.
"""
import asyncio
from loguru import logger
from fastapi import Depends, HTTPException
from fastapi.security.http import HTTPAuthorizationCredentials, HTTPBearer

from app.core.config import EXTRACTOR_SECRET_KEY, API_KEY_WAITING_TIME

bearer = HTTPBearer()


async def authenticate_key(
    authorization: HTTPAuthorizationCredentials = Depends(bearer),
) -> bool:
    """
    API key authentification
    """
    # Parse credentials
    api_key_token = authorization.credentials

    if api_key_token != EXTRACTOR_SECRET_KEY:
        logger.debug(f"Invalid API key token received: {api_key_token}")
        await asyncio.sleep(API_KEY_WAITING_TIME)
        raise HTTPException(status_code=401, detail="Invalid token")

    logger.debug(f"API key authentification ending in {api_key_token[-4:]}")
    return True
