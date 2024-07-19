from fastapi import HTTPException
import pandas as pd
from app.api.platform.models.integrations import (
    PostgresqlCredentials,
)
from loguru import logger
from app.core import config
from typing import Literal
from app.db.mongo import get_mongo_db
from app.services.mongo.tasks import get_total_nb_of_tasks
from app.services.mongo.explore import fetch_flattened_tasks
from app.api.platform.models import Pagination
from sqlalchemy import create_engine


async def get_postgres_credentials_for_org(org_id: str) -> PostgresqlCredentials:
    mongo_db = await get_mongo_db()
    postgres_credentials = await mongo_db["integrations"].find_one(
        {"org_id": org_id},
    )
    if postgres_credentials is None:
        raise HTTPException(
            status_code=400, detail=f"No dedicated database found for org {org_id}"
        )
    # Remove the _id field
    if "_id" in postgres_credentials.keys():
        del postgres_credentials["_id"]

    postgres_credentials_valid = PostgresqlCredentials.model_validate(
        postgres_credentials
    )
    return postgres_credentials_valid


async def update_postgres_status(
    org_id: str, project_id: str, status: Literal["started", "failed", "finished"]
) -> PostgresqlCredentials:
    mongo_db = await get_mongo_db()

    # Credentials have two array fields projects_started and projects_finished
    # We add the project_id to projects_started when the project is started
    # We remove the project_id from projects_started when the project is failed
    # We remove the project_id from projects_started and add it to projects_finished when the project is finished
    if status == "started":
        updated_credentials = await mongo_db["integrations"].find_one_and_update(
            {"org_id": org_id},
            {"$push": {"projects_started": project_id}},
            return_document=True,
        )
    elif status == "failed":
        updated_credentials = await mongo_db["integrations"].find_one_and_update(
            {"org_id": org_id},
            {"$pull": {"projects_started": project_id}},
            return_document=True,
        )
    else:  # status == "finished"
        updated_credentials = await mongo_db["integrations"].find_one_and_update(
            {"org_id": org_id},
            {
                "$pull": {"projects_started": project_id},
                "$push": {"projects_finished": project_id},
            },
            return_document=True,
        )

    return updated_credentials


async def export_project_to_dedicated_postgres(
    project_name: str,
    project_id: str,
    credentials: PostgresqlCredentials,
    debug: bool = False,
) -> Literal["success", "failure"]:
    """
    Export the project to the dedicated Neon Postgres database
    """

    logger.info(
        f"Starting export of project {project_id} to dedicated Postgres {credentials.server}:{credentials.database}"
    )

    # Get the total number of tasks
    total_nb_tasks = await get_total_nb_of_tasks(project_id)

    # Fetch admin credentials
    neon_user = config.NEON_ADMIN_USERNAME
    neon_password = config.NEON_ADMIN_PASSWORD

    if neon_user is None or neon_password is None:
        logger.error("Neon admin credentials are not configured")
        return "failure"

    # Connect to Neon Postgres database, we add asyncpg for async support
    connection_string = f"postgresql://{neon_user}:{neon_password}@{credentials.server}/{credentials.database}"
    engine = create_engine(connection_string, echo=debug)

    logger.debug(f"Connected to Postgres {credentials.server}:{credentials.database}")

    # We batch to avoid memory issues
    batch_size = 1024
    nb_batches = total_nb_tasks // batch_size

    columns = None
    for i in range(nb_batches + 1):
        logger.debug(f"Exporting batch {i} of {nb_batches}")

        flattened_tasks = await fetch_flattened_tasks(
            project_id=project_id,
            limit=batch_size,
            with_events=True,
            with_sessions=True,
            pagination=Pagination(page=i, per_page=batch_size),
        )

        # Convert the list of FlattenedTask to a pandas dataframe
        tasks_df = pd.DataFrame([task.model_dump() for task in flattened_tasks])

        if columns is None:
            columns = tasks_df.columns
        else:
            # Only keep the columns that are in the first batch
            # And remove columns that are not in the first batch
            tasks_df = tasks_df[list(set(columns).intersection(set(tasks_df.columns)))]

        # Upload dataframe to Postgres
        # There should be no need to sleep in between batches, as this connector is synchronous
        pd.DataFrame.to_sql(
            tasks_df,
            project_name,
            engine,
            if_exists="append",
            index=False,
        )
        logger.debug(f"Uploaded batch {i} to Postgres")

    logger.info("Export finished")
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
