import base64
from datetime import datetime
from typing import List, Optional

from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from langfuse import Langfuse  # type: ignore
from langfuse.client import ObservationsViews  # type: ignore
from loguru import logger

from extractor.core import config
from extractor.db.mongo import get_mongo_db
from extractor.models import LogEventForTasks
from extractor.services.connectors.base import BaseConnector
from extractor.services.log.tasks import process_logs_for_tasks
from extractor.services.projects import get_project_by_id


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
        last_langfuse_extract = project.settings.last_langfuse_extract
        if last_langfuse_extract is None:
            return None
        elif isinstance(last_langfuse_extract, datetime):
            return last_langfuse_extract
        elif isinstance(last_langfuse_extract, str):
            try:
                return datetime.strptime(last_langfuse_extract, "%Y-%m-%dT%H:%M:%S.%f")
            except:
                return datetime.strptime(last_langfuse_extract, "%Y-%m-%d %H:%M:%S.%f")
        elif last_langfuse_extract is None:
            return None
        else:
            logger.error(
                f"Error while getting last Langfuse extract for project {self.project_id}: {last_langfuse_extract} is neither a datetime nor a string: {type(last_langfuse_extract)}"
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
        logs_to_process: List[LogEventForTasks] = []
        extra_logs_to_save: List[LogEventForTasks] = []

        if self.observations is None:
            logger.error(
                f"No Langfuse observations to process for project id: {self.project_id}"
            )
            return 0

        for observation in self.observations.data:
            try:
                raw_input = observation.input
                raw_output = observation.output

                input = None
                output = None
                system_prompt = None

                # Input processing
                if isinstance(raw_input, str):
                    input = raw_input
                if isinstance(raw_input, list):
                    # input is a list of messagess
                    user_messages = [
                        m
                        for m in raw_input
                        if isinstance(m, dict) and m.get("role") == "user"
                    ]
                    system_messages = [
                        m
                        for m in raw_input
                        if isinstance(m, dict) and m.get("role") == "system"
                    ]
                    if len(user_messages) > 0:
                        input = user_messages[-1].get("content", None)
                    if len(system_messages) > 0:
                        output = system_messages[-1].get("content", None)

                # Output processing
                if isinstance(raw_output, dict):
                    output = raw_output.get("content", None)
                if isinstance(raw_output, str):
                    output = raw_output

                if input is None:
                    logger.warning(
                        f"Langfuse connector: Found empty input in project {self.project_id} of orga {org_id}: input is None. Skipping. raw_input: {raw_input}"
                    )
                    continue
                if not isinstance(input, str):
                    logger.error(
                        f"Langfuse connector: Found incompatible input while processing project {self.project_id} of orga {org_id}: input is not a string. Skipping. raw_input: {raw_input}"
                    )
                    continue

                log_event = LogEventForTasks(
                    created_at=int(observation.start_time.timestamp()),
                    input=input,
                    output=output,
                    session_id=str(observation.trace_id),
                    project_id=self.project_id,
                    metadata={
                        "langsfuse_run_id": observation.id,
                        "system_prompt": system_prompt,
                        "source": "langfuse",
                    },
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
        await process_logs_for_tasks(
            project_id=self.project_id,
            org_id=org_id,
            logs_to_process=logs_to_process,
            extra_logs_to_save=extra_logs_to_save,
        )

        return len(logs_to_process)
