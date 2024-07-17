import base64
import os
from datetime import datetime
from typing import List, Optional
from app.core import config
from pydantic import BaseModel

from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Hash import SHA256
from langsmith import Client
from loguru import logger

from app.api.v1.models import LogEvent
from app.db.mongo import get_mongo_db
from app.services.connectors.base import BaseConnector
from app.services.log import process_log

from app.services.projects import get_project_by_id


class LangsmithCredentials(BaseModel):
    langsmith_api_key: str
    langsmith_project_name: str


class LangsmithConnector(BaseConnector):
    project_id: str
    credentials: Optional[LangsmithCredentials] = None
    client: Optional[Client] = None

    def __init__(
        self,
        project_id: str,
    ):
        self.project_id = project_id

    async def load_config(
        self,
        langsmith_api_key: Optional[str] = None,
        langsmith_project_name: Optional[str] = None,
    ):
        if langsmith_api_key is not None and langsmith_project_name is not None:
            self.credentials = LangsmithCredentials(
                langsmith_api_key=langsmith_api_key,
                langsmith_project_name=langsmith_project_name,
            )
            self.client = Client(api_key=self.credentials.langsmith_api_key)
            return

        mongo_db = await get_mongo_db()
        encryption_key = config.EXTRACTOR_SECRET_KEY

        # Fetch the encrypted credentials from the database
        credentials = await mongo_db["keys"].find_one(
            {"project_id": self.project_id},
        )

        credentials_data = LangsmithCredentials.model_validate(credentials)

        # Decrypt the credentials
        source = base64.b64decode(credentials_data.langsmith_api_key.encode("latin-1"))

        # use SHA-256 over our key to get a proper-sized AES key
        key = SHA256.new(encryption_key.encode("utf-8")).digest()
        IV = source[: AES.block_size]  # extract the IV from the beginning
        decryptor = AES.new(key, AES.MODE_CBC, IV)
        data = decryptor.decrypt(source[AES.block_size :])  # decrypt the data
        padding = data[-1]  # extract the padding length

        self.credentials = LangsmithCredentials(
            langsmith_api_key=data[:-padding].decode("utf-8"),
            langsmith_project_name=credentials_data.langsmith_project_name,
        )
        self.client = Client(api_key=self.credentials.langsmith_api_key)

    async def register(
        self,
        langsmith_api_key: Optional[str] = None,
        langsmith_project_name: Optional[str] = None,
    ):
        """
        Store the encrypted Langsmith credentials in the database
        """

        if langsmith_api_key is None or langsmith_project_name is None:
            logger.info("No Langsmith credentials provided")
            return

        mongo_db = await get_mongo_db()

        encryption_key = config.EXTRACTOR_SECRET_KEY
        api_key_as_bytes = langsmith_api_key.encode("utf-8")

        # Encrypt the credentials
        # use SHA-256 over our key to get a proper-sized AES key
        key = SHA256.new(encryption_key.encode("utf-8")).digest()

        IV = Random.new().read(AES.block_size)  # generate IV
        encryptor = AES.new(key, AES.MODE_CBC, IV)
        padding = (
            AES.block_size - len(api_key_as_bytes) % AES.block_size
        )  # calculate needed padding
        api_key_as_bytes += bytes([padding]) * padding
        # store the IV at the beginning and encrypt
        data = IV + encryptor.encrypt(api_key_as_bytes)

        # Store the encrypted credentials in the database
        await mongo_db["keys"].update_one(
            {"project_id": self.project_id},
            {
                "$set": {
                    "type": "langsmith",
                    "langsmith_api_key": base64.b64encode(data).decode("latin-1"),
                    "langsmith_project_name": langsmith_project_name,
                },
            },
            upsert=True,
        )

    async def _get_last_langsmith_extract(self) -> Optional[datetime]:
        """
        Get the last Langsmith extract date for a project
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
        runs_as_dict = []
        try:
            # Runs are pydantic model v1
            runs_as_dict = [run.dict() for run in self.runs]
        except Exception as e:
            logger.error(
                f"Error converting runs to dict: {e}. Retrying with model_dump method"
            )
            # Try with pydantic model v2
            runs_as_dict = [run.model_dump() for run in self.runs]

        if len(runs_as_dict) > 0:
            mongo_db["logs_langsmith"].insert_many(runs_as_dict)

    async def pull(self):
        if self.credentials is None:
            raise ValueError("Credentials not loaded")

        last_langsmith_extract = await self._get_last_langsmith_extract()
        if last_langsmith_extract is None:
            self.runs = self.client.list_runs(
                project_name=self.credentials.project_name,
                run_type="llm",
            )
        else:
            self.runs = self.client.list_runs(
                project_name=self.credentials.project_name,
                run_type="llm",
                start_time=datetime.strptime(
                    last_langsmith_extract, "%Y-%m-%d %H:%M:%S.%f"
                ),
            )
        # Save the raw data
        self._dump()

    async def _update_last_langsmith_extract(self):
        """
        Change the last Langsmith extract for a project
        """
        mongo_db = await get_mongo_db()

        await mongo_db["projects"].update_one(
            {"id": self.project_id},
            {"$set": {"settings.last_langsmith_extract": datetime.now()}},
        )

    async def push(
        self,
        org_id: str,
        current_usage: int,
        max_usage: int,
    ):
        logs_to_process: List[LogEvent] = []
        extra_logs_to_save: List[LogEvent] = []

        for run in self.runs:
            try:
                input = ""
                for message in run.inputs["messages"]:
                    if "HumanMessage" in message["id"]:
                        input += message["kwargs"]["content"]

                output = ""
                for generation in run.outputs["generations"]:
                    output += generation["text"]

                if input == "" or output == "":
                    continue

                run_end_time = run.end_time
                if run_end_time:
                    run_end_time_ts = int(run_end_time.timestamp())
                else:
                    run_end_time_ts = None

                log_event = LogEvent(
                    created_at=run_end_time_ts,
                    input=input,
                    output=output,
                    session_id=str(run.session_id),
                    project_id=self.project_id,
                    metadata={"langsmith_run_id": run.id},
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
                    f"Error processing langsmith run for project id: {self.project_id}, {e}"
                )

        await self._update_last_langsmith_extract()

        await process_log(
            project_id=self.project_id,
            org_id=org_id,
            logs_to_process=logs_to_process,
            extra_logs_to_save=extra_logs_to_save,
        )
        logger.debug(
            f"Finished processing langsmith runs for project id: {self.project_id}"
        )

    async def sync(
        self,
        org_id: str,
        current_usage: int,
        max_usage: int,
        langsmith_api_key: Optional[str] = None,
        langsmith_project_name: Optional[str] = None,
    ):
        await self.load_config(
            langsmith_api_key=langsmith_api_key,
            langsmith_project_name=langsmith_project_name,
        )
        await self.pull()
        await self.push(
            org_id=org_id,
            current_usage=current_usage,
            max_usage=max_usage,
        )
        await self.register(
            langsmith_api_key=langsmith_api_key,
            langsmith_project_name=langsmith_project_name,
        )
        return {
            "status": "ok",
            "message": "Langsmith synchronisation pipeline ran successfully",
        }
