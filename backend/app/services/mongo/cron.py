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


async def fetch_and_decrypt_langsmith_credentials(
    project_id: str,
):
    """
    Fetch and decrypt the Langsmith credentials from the database
    """

    mongo_db = await get_mongo_db()
    encryption_key = os.getenv("EXTRACTOR_SECRET_KEY")

    # Fetch the encrypted credentials from the database
    credentials = await mongo_db["keys"].find_one(
        {"project_id": project_id},
    )

    # Decrypt the credentials
    source = base64.b64decode(credentials["langsmith_api_key"].encode("latin-1"))

    key = SHA256.new(
        encryption_key.encode("utf-8")
    ).digest()  # use SHA-256 over our key to get a proper-sized AES key
    IV = source[: AES.block_size]  # extract the IV from the beginning
    decryptor = AES.new(key, AES.MODE_CBC, IV)
    data = decryptor.decrypt(source[AES.block_size :])  # decrypt the data
    padding = data[-1]  # extract the padding length
    logger.debug(
        f"Decrypted Langsmith credentials for project : {data[:-padding].decode('utf-8')}"
    )
    return {
        "langsmith_api_key": data[:-padding].decode("utf-8"),
        "langsmith_project_name": credentials["langsmith_project_name"],
    }


async def encrypt_and_store_langsmith_credentials(
    project_id: str,
    langsmith_api_key: str,
    langsmith_project_name: str,
):
    """
    Store the encrypted Langsmith credentials in the database
    """

    mongo_db = await get_mongo_db()

    encryption_key = os.getenv("EXTRACTOR_SECRET_KEY")
    api_key_as_bytes = langsmith_api_key.encode("utf-8")

    # Encrypt the credentials
    key = SHA256.new(
        encryption_key.encode("utf-8")
    ).digest()  # use SHA-256 over our key to get a proper-sized AES key

    IV = Random.new().read(AES.block_size)  # generate IV
    encryptor = AES.new(key, AES.MODE_CBC, IV)
    padding = (
        AES.block_size - len(api_key_as_bytes) % AES.block_size
    )  # calculate needed padding
    api_key_as_bytes += bytes([padding]) * padding
    data = IV + encryptor.encrypt(
        api_key_as_bytes
    )  # store the IV at the beginning and encrypt

    # Store the encrypted credentials in the database
    await mongo_db["keys"].update_one(
        {"project_id": project_id},
        {
            "$set": {
                "type": "langsmith",
                "langsmith_api_key": base64.b64encode(data).decode("latin-1"),
                "langsmith_project_name": langsmith_project_name,
            },
        },
        upsert=True,
    )


async def fetch_and_decrypt_langfuse_credentials(
    project_id: str,
):
    """
    Fetch and decrypt the Langfuse credentials from the database
    """

    mongo_db = await get_mongo_db()
    encryption_key = os.getenv("EXTRACTOR_SECRET_KEY")

    # Fetch the encrypted credentials from the database
    credentials = await mongo_db["keys"].find_one(
        {"project_id": project_id},
    )

    # Decrypt the credentials
    source = base64.b64decode(credentials["langfuse_secret_key"].encode("latin-1"))

    key = SHA256.new(
        encryption_key.encode("utf-8")
    ).digest()  # use SHA-256 over our key to get a proper-sized AES key
    IV = source[: AES.block_size]  # extract the IV from the beginning
    decryptor = AES.new(key, AES.MODE_CBC, IV)
    data = decryptor.decrypt(source[AES.block_size :])  # decrypt the data
    padding = data[-1]  # extract the padding length
    logger.debug(
        f"Decrypted Langfuse credentials for project : {data[:-padding].decode('utf-8')}"
    )
    return {
        "langfuse_secret_key": data[:-padding].decode("utf-8"),
        "langfuse_public_key": credentials["langfuse_public_key"],
    }


async def encrypt_and_store_langfuse_credentials(
    project_id: str,
    langfuse_secret_key: str,
    langfuse_public_key: str,
):
    """
    Store the encrypted Langsmith credentials in the database
    """

    mongo_db = await get_mongo_db()

    encryption_key = os.getenv("EXTRACTOR_SECRET_KEY")
    api_key_as_bytes = langfuse_secret_key.encode("utf-8")

    # Encrypt the credentials
    key = SHA256.new(
        encryption_key.encode("utf-8")
    ).digest()  # use SHA-256 over our key to get a proper-sized AES key

    IV = Random.new().read(AES.block_size)  # generate IV
    encryptor = AES.new(key, AES.MODE_CBC, IV)
    padding = (
        AES.block_size - len(api_key_as_bytes) % AES.block_size
    )  # calculate needed padding
    api_key_as_bytes += bytes([padding]) * padding
    data = IV + encryptor.encrypt(
        api_key_as_bytes
    )  # store the IV at the beginning and encrypt

    # Store the encrypted credentials in the database
    await mongo_db["keys"].update_one(
        {"project_id": project_id},
        {
            "$set": {
                "type": "langfuse",
                "langfuse_secret_key": base64.b64encode(data).decode("latin-1"),
                "langfuse_public_key": langfuse_public_key,
            },
        },
        upsert=True,
    )
