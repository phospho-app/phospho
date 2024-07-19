from typing import List, Literal, Optional

import pandas as pd
from app.api.platform.models import Pagination
from app.core import config
from app.db.mongo import get_mongo_db
from app.services.mongo.explore import fetch_flattened_tasks
from app.services.mongo.tasks import get_total_nb_of_tasks
from app.utils import slugify_string
from fastapi import HTTPException
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import create_engine


class PostgresqlCredentials(BaseModel, extra="allow"):
    org_id: str
    server: str
    database: str
    username: str
    password: str
    # Projects that have started exporting are stored here
    projects_started: List[str] = Field(default_factory=list)
    # Projects that have finished exporting are stored here
    projects_finished: List[str] = Field(default_factory=list)


class PostgresqlIntegration:
    """
    Class to export a project to a dedicated Postgres database
    """

    credentials: Optional[PostgresqlCredentials] = None

    def __init__(
        self,
        org_id: str,
        project_id: Optional[str] = None,
        org_metadata: Optional[dict] = None,
    ):
        self.org_id = org_id
        self.project_id = project_id
        if org_metadata is not None:
            # Verify that the org has access to a dedicated Postgres database, based on the metadata
            if not org_metadata.get("power_bi", False):
                raise HTTPException(
                    status_code=400,
                    detail=f"The organization {org_id} does'nt have access to this feature. Please reach out.",
                )

    async def load_config(self):
        if self.credentials is not None:
            return self.credentials
        mongo_db = await get_mongo_db()
        postgres_credentials = await mongo_db["integrations"].find_one(
            {"org_id": self.org_id},
        )
        if postgres_credentials is not None:
            # Remove the _id field
            if "_id" in postgres_credentials.keys():
                del postgres_credentials["_id"]

            postgres_credentials_valid = PostgresqlCredentials.model_validate(
                postgres_credentials
            )
            self.credentials = postgres_credentials_valid

        # TODO : Create credentials if they don't exist
        # For now, we raise an exception
        raise HTTPException(
            status_code=400,
            detail=f"No dedicated database found for org {self.org_id}",
        )

    async def update_status(
        self,
        status: Literal["started", "failed", "finished"],
    ) -> PostgresqlCredentials:
        mongo_db = await get_mongo_db()

        # Credentials have two array fields projects_started and projects_finished
        # We add the project_id to projects_started when the project is started
        # We remove the project_id from projects_started when the project is failed
        # We remove the project_id from projects_started and add it to projects_finished when the project is finished
        if status == "started":
            updated_credentials = await mongo_db["integrations"].find_one_and_update(
                {"org_id": self.org_id},
                {"$push": {"projects_started": self.project_id}},
                return_document=True,
            )
        elif status == "failed":
            updated_credentials = await mongo_db["integrations"].find_one_and_update(
                {"org_id": self.org_id},
                {"$pull": {"projects_started": self.project_id}},
                return_document=True,
            )
        else:  # status == "finished"
            updated_credentials = await mongo_db["integrations"].find_one_and_update(
                {"org_id": self.org_id},
                {
                    "$pull": {"projects_started": self.project_id},
                    "$push": {"projects_finished": self.project_id},
                },
                return_document=True,
            )

        return updated_credentials

    async def export_project_to_dedicated_postgres(
        self,
        exported_db_name: str,
        batch_size: int = 1024,
    ) -> Literal["success", "failure"]:
        """
        Export the project to the dedicated Postgres database
        """
        if self.project_id is None:
            logger.error("No project_id provided")
            return "failure"
        await self.update_status("started")
        await self.load_config()
        if self.credentials is None:
            logger.error("No credentials found")
            await self.update_status("failed")
            return "failure"

        exported_db_name = slugify_string(exported_db_name)
        logger.info(
            f"Starting export of project {self.project_id} to dedicated Postgres {self.credentials.server}:{self.credentials.database}"
        )
        # Get the total number of tasks
        total_nb_tasks = await get_total_nb_of_tasks(self.project_id)
        if total_nb_tasks is None or total_nb_tasks == 0:
            logger.error("No tasks found in the project")
            await self.update_status("finished")
            return "success"

        # Fetch admin credentials
        neon_user = config.NEON_ADMIN_USERNAME
        neon_password = config.NEON_ADMIN_PASSWORD

        if neon_user is None or neon_password is None:
            logger.error("Neon admin credentials are not configured")
            await self.update_status("failed")
            return "failure"

        # Connect to Neon Postgres database, we add asyncpg for async support
        debug = config.ENVIRONMENT == "test"
        connection_string = f"postgresql://{neon_user}:{neon_password}@{self.credentials.server}/{self.credentials.database}"
        engine = create_engine(connection_string, echo=debug)

        logger.debug(
            f"Connected to Postgres {self.credentials.server}:{self.credentials.database}"
        )
        nb_batches = total_nb_tasks // batch_size
        columns = None
        for i in range(nb_batches + 1):
            logger.debug(f"Exporting batch {i}/{nb_batches} ({batch_size} tasks)")
            flattened_tasks = await fetch_flattened_tasks(
                project_id=self.project_id,
                limit=batch_size,
                with_events=True,
                with_sessions=True,
                pagination=Pagination(page=i, per_page=batch_size),
            )
            # Convert the list of FlattenedTask to a pandas dataframe
            tasks_df = pd.DataFrame([task.model_dump() for task in flattened_tasks])
            # The metadata columns depends on the tasks. To avoid creating a wrong schema, we only create the schema with the first batch
            # Then we only keep the columns that are in the first batch
            if columns is None:
                columns = tasks_df.columns
            else:
                # Only keep the columns that are in the first batch and remove columns that are not in the first batch
                tasks_df = tasks_df[
                    list(set(columns).intersection(set(tasks_df.columns)))
                ]
            # Upload dataframe to Postgresql. No need to sleep in between batches, as this connector is synchronous
            pd.DataFrame.to_sql(
                tasks_df,
                exported_db_name,
                engine,
                if_exists="append",
                index=False,
            )
            logger.debug("Batch uploaded to Postgres")

        logger.info("Export finished")
        await self.update_status("finished")
        return "success"


"""
The function below is a work in progress to convert a Pydantic model to a SQLModel
Could be usefull later
"""

# def pydantic_to_sqlmodel(pydantic_model: BaseModel) -> Type[SQLModel]:
#     class_name = pydantic_model.__name__
#     columns = {}

#     for field_name, field in pydantic_model.model_fields.items():
#         field_type = field.annotation

#         string_field_type = str(field_type)

#         nullable = "Optional" in string_field_type

#         if "dict" in string_field_type or "Literal" in string_field_type:
#             continue

#         if field_name == "task_id":
#             columns[field_name] = (str, Field(primary_key=True))
#         else:
#             if "str" in string_field_type:
#                 columns[field_name] = (
#                     Optional[str] if nullable else str,
#                     Field(default=None, nullable=nullable),
#                 )
#             elif "int" in string_field_type:
#                 columns[field_name] = (
#                     Optional[int] if nullable else int,
#                     Field(default=None, nullable=nullable),
#                 )
#             elif "float" in string_field_type:
#                 columns[field_name] = (
#                     Optional[float] if nullable else float,
#                     Field(default=None, nullable=nullable),
#                 )
#             elif "bool" in string_field_type:
#                 columns[field_name] = (
#                     Optional[bool] if nullable else bool,
#                     Field(default=None, nullable=nullable),
#                 )
#             else:
#                 logger.warning(
#                     f"Field {field_name} has unknown type {string_field_type}"
#                 )
#         logger.debug(
#             f"Added column {field_name} with type {string_field_type}, nullable {nullable}"
#         )

#     logger.debug(f"Creating SQLModel {class_name} with columns {columns}")
#     dynamic_class = create_model(
#         class_name,
#         __base__=SQLModel,
#         __cls_kwargs__={"table": True, "extend_existing": True},
#         **columns,
#     )
#     logger.debug(f"Created SQLModel {dynamic_class}")
#     return dynamic_class
