from typing import List, Literal, Optional

import pandas as pd
from app.api.platform.models import Pagination
from app.core import config
from app.db.mongo import get_mongo_db
from app.services.mongo.tasks import fetch_flattened_tasks, get_total_nb_of_tasks
from app.utils import generate_uuid, slugify_string
from fastapi import HTTPException
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import create_engine
from sqlalchemy.sql import text


class PostgresqlCredentials(BaseModel, extra="allow"):
    org_id: str
    org_name: str
    type: str = "postgresql"  # integration type
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
        org_name: str,
        project_id: Optional[str] = None,
        project_name: Optional[str] = None,
        org_metadata: Optional[dict] = None,
    ):
        """
        This class exports a project to a dedicated Postgres database.
        """
        self.org_id = org_id
        if self.org_id is None:
            raise ValueError("No org_id provided")
        self.org_name = org_name
        if self.org_name is None:
            raise ValueError("No org_name provided")

        self.project_id = project_id
        self.project_name = project_name
        if org_metadata is not None:
            # Verify that the org has access to a dedicated Postgres database, based on the metadata
            if not org_metadata.get("power_bi", False):
                raise HTTPException(
                    status_code=400,
                    detail=f"The organization {org_id} doesn't have access to this feature. Please reach out.",
                )

        if config.SQLDB_CONNECTION_STRING is None:
            logger.error("Neon admin credentials are not configured")
            raise HTTPException(
                status_code=500,
                detail="Admin credentials are not configured",
            )

    def _connection_string(self) -> str:
        # TODO : Add custom connection string in the credentials so that this write operation
        # can be done on a different database
        if self.credentials is None:
            raise ValueError("No credentials found")
        return f"{config.SQLDB_CONNECTION_STRING}/{self.credentials.database}"

    async def load_config(self):
        """
        Load the Postgres credentials from MongoDB.

        If the credentials are not found, create them. The database name is the slugified org name. The org name
        is unique to each organization.

        This drops the database if it already exists and creates a new one.
        """
        if self.credentials is not None:
            logger.info(f"Credentials already loaded for {self.org_id}")
            return self.credentials
        mongo_db = await get_mongo_db()
        postgres_credentials = await mongo_db["integrations"].find_one(
            {"org_id": self.org_id},
        )
        if postgres_credentials is not None:
            # Remove the _id field
            if "_id" in postgres_credentials.keys():
                del postgres_credentials["_id"]
            if "type" not in postgres_credentials.keys():
                postgres_credentials["type"] = "postgresql"
                # update type in MongoDB
                await mongo_db["integrations"].update_one(
                    {"org_id": self.org_id},
                    {"$set": {"type": postgres_credentials["type"]}},
                )
            if "org_name" not in postgres_credentials.keys():
                postgres_credentials["org_name"] = self.org_name
                # update org_name in MongoDB
                await mongo_db["integrations"].update_one(
                    {"org_id": self.org_id},
                    {"$set": {"org_name": postgres_credentials["org_name"]}},
                )

            postgres_credentials_valid = PostgresqlCredentials.model_validate(
                postgres_credentials
            )
            self.credentials = postgres_credentials_valid
            return

        # Create database using the connection to the default database
        engine = create_engine(f"{config.SQLDB_CONNECTION_STRING}/phospho")
        database = slugify_string(self.org_name)
        # Create the database if it doesn't exist
        with engine.connect() as connection:
            logger.debug(f"Creating database {slugify_string(self.org_name)}")
            connection.execution_options(isolation_level="AUTOCOMMIT")
            # UPDATE pg_database SET datallowconn = 'false' WHERE datname = 'databasename';
            # SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'databasename';
            try:
                connection.execute(
                    text(f"DROP DATABASE IF EXISTS {slugify_string(self.org_name)};")
                )
            except Exception as e:
                # Carry on
                logger.error(e)
            try:
                connection.execute(
                    text(f"CREATE DATABASE {slugify_string(self.org_name)};")
                )
            except Exception as e:
                # Carry on
                logger.error(e)

        # Connect to the new database
        engine = create_engine(f"{config.SQLDB_CONNECTION_STRING}/{database}")
        with engine.connect() as connection:
            # Create a new user if it doesn't exist
            username = f"user_{generate_uuid()[:8]}"
            password = generate_uuid()
            connection.execute(text(f"DROP USER IF EXISTS {username};"))
            connection.execute(
                text(f"CREATE USER {username} WITH PASSWORD '{password}';")
            )
            # Grant all privileges to the user over the database
            connection.execute(
                text(
                    f"GRANT ALL PRIVILEGES ON DATABASE {slugify_string(self.org_name)} TO {username};"
                )
            )
            # Grant the select privilege to the user to current tables
            connection.execute(
                text(f"GRANT SELECT ON ALL TABLES IN SCHEMA public TO {username};")
            )
            # Grant the select privilege to the user to future tables
            connection.execute(
                text(
                    f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO {username};;"
                )
            )
            # The context manager will commit and close the connection

        # Get the server from the connection string
        server = config.SQLDB_CONNECTION_STRING.split("@")[1]
        self.credentials = PostgresqlCredentials(
            org_id=self.org_id,
            org_name=self.org_name,
            type="postgresql",
            server=server,
            database=slugify_string(self.org_name),
            username=username,
            password=password,
        )
        # Push to MongoDB
        await mongo_db["integrations"].update_one(
            {"org_id": self.org_id},
            {"$set": self.credentials.model_dump()},
            upsert=True,
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
                {"$addToSet": {"projects_started": self.project_id}},
                return_document=True,
            )
        elif status == "failed":
            updated_credentials = await mongo_db["integrations"].find_one_and_update(
                {"org_id": self.org_id},
                {"$pull": {"projects_started": self.project_id}},
                return_document=True,
            )
        elif status == "finished":
            updated_credentials = await mongo_db["integrations"].find_one_and_update(
                {"org_id": self.org_id},
                {
                    "$pull": {"projects_started": self.project_id},
                    "$addToSet": {"projects_finished": self.project_id},
                },
                return_document=True,
            )
        else:
            raise ValueError(f"Unknown status {status}")

        return updated_credentials

    async def push(
        self,
        batch_size: int = 256,
    ) -> Literal["success", "failure"]:
        """
        Export the project to the dedicated Postgres database.

        This replaces the table if it already exists.

        The table name is the slugified project name.
        """
        if self.project_id is None:
            logger.error("No project_id provided")
            return "failure"
        if self.project_name is None:
            logger.error("No project_name provided")
            return "failure"
        await self.update_status("started")
        await self.load_config()
        if self.credentials is None:
            logger.error("No credentials found")
            await self.update_status("failed")
            return "failure"

        logger.info(
            f"Starting export of project {self.project_id} to dedicated Postgres {self.credentials.server}:{self.credentials.database}"
        )
        # Get the total number of tasks
        total_nb_tasks = await get_total_nb_of_tasks(self.project_id)
        if total_nb_tasks is None or total_nb_tasks == 0:
            logger.error("No tasks found in the project")
            await self.update_status("finished")
            return "success"

        # Connect to Neon Postgres database, we add asyncpg for async support
        debug = config.ENVIRONMENT == "test"
        try:
            engine = create_engine(self._connection_string(), echo=debug)
            with engine.connect() as connection:
                logger.debug(
                    f"Connected to Postgres {self.credentials.server}:{self.credentials.database}"
                )
                nb_batches = total_nb_tasks // batch_size
                columns = None
                for i in range(nb_batches + 1):
                    logger.debug(
                        f"Exporting batch {i}/{nb_batches} ({batch_size} tasks)"
                    )
                    flattened_tasks = await fetch_flattened_tasks(
                        project_id=self.project_id,
                        limit=batch_size,
                        with_events=True,
                        with_sessions=True,
                        pagination=Pagination(page=i, per_page=batch_size),
                        sort_get_most_recent=False,
                    )
                    # Convert the list of FlattenedTask to a pandas dataframe
                    tasks_df = pd.DataFrame(
                        [task.model_dump() for task in flattened_tasks]
                    )
                    # The metadata columns depends on the tasks. To avoid creating a wrong schema, we only create the schema with the first batch
                    # Then we only keep the columns that are in the first batch
                    if columns is None:
                        columns = tasks_df.columns
                    else:
                        # Only keep the columns that are in the first batch and remove columns that are not in the first batch
                        tasks_df = tasks_df[
                            list(set(columns).intersection(set(tasks_df.columns)))
                        ]
                    if_exists_mode: Literal["replace", "append"] = (
                        "replace" if i == 0 else "append"
                    )
                    # Note: to_sql is not async, we could use asyncpg directly: https://github.com/MagicStack/asyncpg
                    pd.DataFrame.to_sql(
                        tasks_df,
                        slugify_string(self.project_name),
                        connection,
                        if_exists=if_exists_mode,
                        index=False,
                    )
                    logger.debug("Batch uploaded to Postgres")

                connection.close()

            logger.info("Export finished")
            await self.update_status("finished")
            return "success"
        except Exception as e:
            logger.error(e)
            await self.update_status("failed")
            return "failure"


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
