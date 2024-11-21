from typing import List, Literal, Optional

from app.services.mongo.dataviz import collect_unique_metadata_fields
import pandas as pd
from app.api.platform.models import Pagination
from app.core import config, constants
from app.db.mongo import get_mongo_db
from app.services.mongo.tasks import fetch_flattened_tasks, get_total_nb_of_tasks
from app.utils import generate_uuid, slugify_string
from fastapi import HTTPException
from loguru import logger
from pydantic import BaseModel, Field
from sqlalchemy import create_engine
from sqlalchemy.sql import text
from datetime import datetime
from phospho.models import ProjectDataFilters, FlattenedTask
from tqdm import tqdm


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
    last_updated: Optional[datetime] = None


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
            logger.debug(f"Creating database {database}")
            connection.execution_options(isolation_level="AUTOCOMMIT")
            # UPDATE pg_database SET datallowconn = 'false' WHERE datname = 'databasename';
            # SELECT pg_terminate_backend(pid) FROM pg_stat_activity WHERE datname = 'databasename';
            try:
                connection.execute(text(f"DROP DATABASE IF EXISTS {database};"))
            except Exception as e:
                # Carry on
                logger.error(e)
            try:
                connection.execute(text(f"CREATE DATABASE {database};"))
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
                text(f"GRANT ALL PRIVILEGES ON DATABASE {database} TO {username};")
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
                    "$set": {"last_updated": datetime.now()},
                },
                return_document=True,
            )
        else:
            raise ValueError(f"Unknown status {status}")

        return updated_credentials

    async def _get_number_category_metadata_fields(self):
        """
        This is a helper function to get the unique metadata fields from the tasks
        currently in the MongoDB project.
        """
        # To create the metadata fields, we need to get the unique metadata fields from the tasks
        category_metadata_fields = constants.RESERVED_CATEGORY_METADATA_FIELDS
        number_metadata_fields = constants.RESERVED_NUMBER_METADATA_FIELDS

        category_metadata_fields = (
            category_metadata_fields
            + await collect_unique_metadata_fields(
                project_id=self.project_id, type="string"
            )
        )
        number_metadata_fields = (
            number_metadata_fields
            + await collect_unique_metadata_fields(
                project_id=self.project_id, type="number"
            )
        )

        # Deduplicate the metadata fields
        category_metadata_fields = list(set(category_metadata_fields))
        number_metadata_fields = list(set(number_metadata_fields))

        # Sort the metadata fields
        category_metadata_fields.sort()
        number_metadata_fields.sort()

        return category_metadata_fields, number_metadata_fields

    def table_name(self):
        return slugify_string(self.project_name)

    async def create_table(self):
        """
        Create the table in the dedicated Postgres database.
        """
        logger.info(
            f"Creating table for project {self.project_id} {self.project_name}: {self.credentials.database}.{self.table_name()}"
        )
        (
            category_metadata_fields,
            number_metadata_fields,
        ) = await self._get_number_category_metadata_fields()
        # Turn this into a string to be able to store it in the database
        # Note: this ends with a comma
        task_metadata_string = ""
        for field in category_metadata_fields:
            task_metadata_string += f'"task_metadata.{field}" TEXT,\n'
        for field in number_metadata_fields:
            task_metadata_string += f'"task_metadata.{field}" FLOAT,\n'

        engine = create_engine(
            f"{config.SQLDB_CONNECTION_STRING}/{self.credentials.database}"
        )
        with engine.connect() as connection:
            connection.execute(
                text(
                    f"""CREATE TABLE IF NOT EXISTS {self.table_name()} (
                task_id VARCHAR(255) PRIMARY KEY NOT NULL,
                task_input TEXT,
                task_output TEXT,
                task_eval VARCHAR(255),
                task_eval_source VARCHAR(255),
                task_eval_at TIMESTAMP,
                task_created_at TIMESTAMP,
                {task_metadata_string} 
                session_id VARCHAR(255),
                task_position INTEGER,
                session_length INTEGER,
                event_name VARCHAR(255),
                event_created_at TIMESTAMP,
                event_confirmed BOOLEAN,
                event_score_range_value FLOAT,
                event_score_range_min FLOAT,
                event_score_range_max FLOAT,
                event_score_range_score_type VARCHAR(255),
                event_score_range_label VARCHAR(255),
                event_source VARCHAR(255),
                event_categories TEXT
                );
                """
                )
            )

    async def update_table_columns(self):
        """
        Fetch all the column names in the SQL table.
        If some task_metadata columns are missing, add them to the table.
        """
        logger.info(
            f"Updating table for project {self.project_id} {self.project_name}: {self.credentials.database}.{self.table_name()}"
        )
        (
            category_metadata_fields,
            number_metadata_fields,
        ) = await self._get_number_category_metadata_fields()

        engine = create_engine(
            f"{config.SQLDB_CONNECTION_STRING}/{self.credentials.database}"
        )

        with engine.connect() as connection:
            # Get the columns in the table
            columns = connection.execute(
                text(
                    f"SELECT column_name FROM information_schema.columns WHERE table_name = '{self.table_name()}';"
                )
            )
            columns = [column[0] for column in columns]
            # Add the missing columns
            for field in category_metadata_fields:
                if f"task_metadata.{field}" not in columns:
                    logger.info(f"Adding category task_metadata field {field} ")
                    connection.execute(
                        text(
                            f'ALTER TABLE {self.table_name()} ADD COLUMN "task_metadata.{field}" TEXT;'
                        )
                    )
            for field in number_metadata_fields:
                if f"task_metadata.{field}" not in columns:
                    logger.info(f"Adding number task_metadata field {field}")
                    connection.execute(
                        text(
                            f'ALTER TABLE {self.table_name()} ADD COLUMN "task_metadata.{field}" FLOAT;'
                        )
                    )

    async def table_exists(self) -> bool:
        """
        Check if the table exists in the dedicated Postgres database.
        """
        logger.info("Checking if table exists")
        engine = create_engine(self._connection_string())
        with engine.connect() as connection:
            result = connection.execute(
                text(
                    f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{self.table_name()}');"
                )
            )

        # Cast the result to a boolean
        return bool(result.scalar())

    async def push(
        self,
        batch_size: int = 256,
        only_new: bool = True,
        fetch_from_flattened_tasks: bool = True,
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
        # Create the filters
        if only_new and self.credentials.last_updated is not None:
            logger.info(
                f"Exporting tasks created after {self.credentials.last_updated}"
            )
            filters = ProjectDataFilters(
                created_at_start=int(self.credentials.last_updated.timestamp())
                if self.credentials.last_updated is not None
                else None
            )
        else:
            logger.info("Exporting all tasks")
            filters = ProjectDataFilters()

        # Get the total number of tasks
        if not fetch_from_flattened_tasks:
            total_nb_tasks = await get_total_nb_of_tasks(
                project_id=self.project_id,
                filters=filters,
            )
            if total_nb_tasks is None or total_nb_tasks == 0:
                logger.error("No tasks found in the project")
                await self.update_status("finished")
                return "success"
        else:
            # This is the number of flattened tasks in the MongoDB
            logger.info(
                f"Fetching the existing flattened_tasks_{self.project_id} from Mongo"
            )
            mongo_db = await get_mongo_db()
            total_nb_tasks = await mongo_db[
                f"flattened_tasks_{self.project_id}"
            ].count_documents()
            if not total_nb_tasks:
                logger.error(
                    f"No flattened tasks found in the project. Populate the collection flattened_tasks_{self.project_id} using the script create_temp_table.ipynb"
                )
                await self.update_status("failed")
                return "failure"

        logger.info(
            f"Total number of tasks to export: {total_nb_tasks}. Batch size: {batch_size}"
        )
        # Check if the table exists
        if not await self.table_exists():
            await self.create_table()
        else:
            await self.update_table_columns()

        # Connect to Neon Postgres database, we add asyncpg for async support
        debug = config.ENVIRONMENT == "test"
        try:
            logger.debug(
                f"Connected to Postgres {self.credentials.server}:{self.credentials.database}"
            )
            engine = create_engine(self._connection_string(), echo=debug)
            nb_batches = total_nb_tasks // batch_size
            columns = None
            for i in tqdm(range(nb_batches + 1)):
                if not fetch_from_flattened_tasks:
                    raw_flattened_tasks = await fetch_flattened_tasks(
                        project_id=self.project_id,
                        limit=batch_size,
                        with_events=True,
                        with_sessions=True,
                        pagination=Pagination(page=i, per_page=batch_size),
                        sort_get_most_recent=False,
                        filters=filters,
                    )
                    flattened_tasks = [
                        task.model_dump() for task in raw_flattened_tasks
                    ]
                else:
                    # Alternative: Directly fetch the flattened tasks from the database
                    # You need to run the scripts/create_temp_table.ipynb to store the flattened_tasks before
                    mongo_db = await get_mongo_db()
                    stored_flattened_tasks = (
                        await mongo_db[f"flattened_tasks_{self.project_id}"]
                        .aggregate(
                            [
                                {"$skip": i * batch_size},
                                {"$limit": batch_size},
                            ]
                        )
                        .to_list(length=batch_size)
                    )

                    new_flattened_tasks = []
                    for task in stored_flattened_tasks:
                        # Remove the _id field
                        if "_id" in task.keys():
                            del task["_id"]

                        # Clean input and output
                        if "task_input" in task.keys():
                            task["task_input"] = task["task_input"].replace("\x00", "")
                        if "task_output" in task.keys():
                            task["task_output"] = task["task_output"].replace(
                                "\x00", ""
                            )

                        # Flatten the task_metadata field into multiple task_metadata.{key} fields
                        if "task_metadata" in task.keys():
                            for key, value in task["task_metadata"].items():
                                if not isinstance(value, dict) and not isinstance(
                                    value, list
                                ):
                                    task[f"task_metadata.{key}"] = value
                                else:
                                    # TODO: Handle nested fields. For now, cast to string
                                    task[f"task_metadata.{key}"] = str(value)
                            del task["task_metadata"]
                        # Convert to a FlattenedTask model
                        new_task = FlattenedTask.model_validate(task)
                        new_flattened_tasks.append(new_task.model_dump())

                    flattened_tasks = new_flattened_tasks

                # Cast event_categories to string (it's a list)
                for task in flattened_tasks:
                    if task["event_categories"] is not None:
                        task["event_categories"] = str(task["event_categories"])

                # Convert the list of FlattenedTask to a pandas dataframe
                tasks_df = pd.DataFrame(flattened_tasks)
                if columns is None:
                    columns = tasks_df.columns
                else:
                    # Only keep the columns that are in the first batch and remove columns that are not in the first batch
                    tasks_df = tasks_df[
                        list(set(columns).intersection(set(tasks_df.columns)))
                    ]

                with engine.connect() as connection:
                    # Note: to_sql is not async, we could use asyncpg directly: https://github.com/MagicStack/asyncpg
                    pd.DataFrame.to_sql(
                        tasks_df,
                        self.table_name(),
                        connection,
                        if_exists="append",
                        index=False,
                    )

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
