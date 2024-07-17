from app.db.mongo import get_mongo_db
from loguru import logger
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
import os
import base64
from Crypto import Random


async def fetch_projects_to_sync(type: str = "langsmith"):
    """
    Fetch the project ids to sync
    """
    mongo_db = await get_mongo_db()
    project_ids = await mongo_db["keys"].distinct("project_id", {"type": type})
    return project_ids
