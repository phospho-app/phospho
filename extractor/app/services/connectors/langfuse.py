import base64
from datetime import datetime
from typing import List, Optional

from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from langfuse import Langfuse
from langfuse.client import ObservationsViews
from loguru import logger

from app.api.v1.models import LogEvent
from app.core import config
from app.db.mongo import get_mongo_db
from app.services.connectors.base import BaseConnector
from app.services.log import process_log
from app.services.projects import get_project_by_id


class LangfuseConnector(BaseConnector):
    project_id: str
    langfuse: Optional[Langfuse] = None
    observations: Optional[ObservationsViews] = None

    def __init__(
        self,
        project_id: str,
        langfuse_public_key: Optional[str] = None,
        langfuse_secret_key: Optional[str] = None,
    ):
        self.project_id = project_id
        self.langfuse_public_key = langfuse_public_key
        self.langfuse_secret_key = langfuse_secret_key

    async def load_config(self):
        """
        Fetch and decrypt the Langfuse credentials from the database
        """

        if (
            self.langfuse_public_key is not None
            and self.langfuse_secret_key is not None
        ):
            logger.info("Langfuse credentials already provided")
            return

        mongo_db = await get_mongo_db()
        encryption_key = config.EXTRACTOR_SECRET_KEY

        # Fetch the encrypted credentials from the database
        credentials = await mongo_db["keys"].find_one(
            {"project_id": self.project_id},
        )

        # Decrypt the credentials
        langfuse_secret_key = credentials.get("langfuse_secret_key", None)
        source = base64.b64decode(langfuse_secret_key.encode("latin-1"))

        key = SHA256.new(
            encryption_key.encode("utf-8")
        ).digest()  # use SHA-256 over our key to get a proper-sized AES key
        IV = source[: AES.block_size]  # extract the IV from the beginning
        decryptor = AES.new(key, AES.MODE_CBC, IV)
        data = decryptor.decrypt(source[AES.block_size :])  # decrypt the data
        padding = data[-1]  # extract the padding length

        self.langfuse_public_key = credentials.get("langfuse_public_key", None)
        self.langfuse_secret_key = data[:-padding].decode("utf-8")

    async def save_config(self):
        """
        Store the encrypted LangFuse credentials in the database
        """
        if self.langfuse_secret_key is None or self.langfuse_public_key is None:
            logger.info("No Langfuse credentials provided")
            return

        mongo_db = await get_mongo_db()

        encryption_key = config.EXTRACTOR_SECRET_KEY
        if not encryption_key:
            logger.error("No encryption key provided")
            return

        api_key_as_bytes = self.langfuse_secret_key.encode("utf-8")

        # Encrypt the credentials
        # use SHA-256 over our key to get a proper-sized AES key
        key = SHA256.new(encryption_key.encode("utf-8")).digest()

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
            {"project_id": self.project_id},
            {
                "$set": {
                    "type": "langfuse",
                    "langfuse_secret_key": base64.b64encode(data).decode("latin-1"),
                    "langfuse_public_key": self.langfuse_public_key,
                },
            },
            upsert=True,
        )

    async def _get_last_langfuse_extract(self) -> Optional[datetime]:
        """
        Get the last Langfuse extract date for a project
        """
        project = await get_project_by_id(self.project_id)
        last_langsmith_extract = project.settings.last_langsmith_extract
        if isinstance(last_langsmith_extract, datetime):
            return last_langsmith_extract
        elif isinstance(last_langsmith_extract, str):
            return datetime.strptime(last_langsmith_extract, "%Y-%m-%d %H:%M:%S.%f")
        else:
            logger.error(
                f"Error while getting last Langsmith extract for project {self.project_id}: {last_langsmith_extract} is neither a datetime nor a string"
            )
            return None

    async def _dump(self):
        # Dump to a dedicated db
        mongo_db = await get_mongo_db()
        observations_list = [
            observation.dict() for observation in self.observations.data
        ]
        if len(observations_list) > 0:
            mongo_db["logs_langfuse"].insert_many(observations_list)

    async def pull(self):
        if self.langfuse_public_key is None or self.langfuse_secret_key is None:
            logger.info("No Langfuse credentials provided")
            return

        self.langfuse = Langfuse(
            public_key=self.langfuse_public_key,
            secret_key=self.langfuse_secret_key,
        )
        last_langfuse_extract = await self._get_last_langfuse_extract()
        if last_langfuse_extract is None:
            self.observations = self.langfuse.client.observations.get_many(
                type="GENERATION"
            )
        else:
            self.observations = self.langfuse.client.observations.get_many(
                type="GENERATION",
                from_start_time=last_langfuse_extract,
            )

        self.langfuse.shutdown()
        # Save the raw data
        await self._dump()

    async def _update_last_langfuse_extract(self):
        """
        Change the last LangFuse extract for a project
        """
        mongo_db = await get_mongo_db()

        await mongo_db["projects"].update_one(
            {"id": self.project_id},
            {"$set": {"settings.last_langfuse_extract": datetime.now()}},
        )

    async def process(
        self,
        org_id: str,
        current_usage: int,
        max_usage: Optional[int] = None,
    ) -> int:
        logs_to_process: List[LogEvent] = []
        extra_logs_to_save: List[LogEvent] = []

        if self.observations is None:
            logger.error(
                f"No Langfuse observations to process for project id: {self.project_id}"
            )
            return 0

        for observation in self.observations.data:
            try:
                input = observation.input
                output = observation.output

                log_event = LogEvent(
                    created_at=int(observation.start_time.timestamp()),
                    input=input,
                    output=output,
                    session_id=str(observation.trace_id),
                    project_id=self.project_id,
                    metadata={"langsfuse_run_id": observation.id},
                    org_id=org_id,
                )

                if max_usage is None or (
                    max_usage is not None and current_usage < max_usage
                ):
                    logs_to_process.append(log_event)
                    current_usage += 1
                else:
                    extra_logs_to_save.append(log_event)
            except Exception as e:
                logger.error(
                    f"Error processing langfuse run for project id: {self.project_id}, {e}"
                )

        await self._update_last_langfuse_extract()
        await process_log(
            project_id=self.project_id,
            org_id=org_id,
            logs_to_process=logs_to_process,
            extra_logs_to_save=extra_logs_to_save,
        )

        return len(logs_to_process)
