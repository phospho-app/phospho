import datetime
from typing import List, Optional

from app.api.platform.models.projects import EmailUsersQuery
import pandas as pd  # type: ignore
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    UploadFile,
)
from google.cloud.storage import Bucket  # type: ignore
from langfuse import Langfuse  # type: ignore
from loguru import logger
from propelauth_fastapi import User  # type: ignore

from app.api.platform.models import (
    AddEventsQuery,
    ConnectLangfuseQuery,
    ConnectLangsmithQuery,
    Events,
    Project,
    ProjectDataFilters,
    ProjectUpdateRequest,
    QuerySessionsTasksRequest,
    QueryUserMetadataRequest,
    Sessions,
    Tasks,
    Users,
)
from app.api.platform.models.explore import Sorting
from app.core import config
from app.security.authentification import (
    propelauth,
    verify_if_propelauth_user_can_access_project,
)
from app.security.authorization import get_quota
from app.services.mongo.events import get_all_events
from app.services.mongo.extractor import ExtractorClient
from app.services.mongo.files import process_file_upload_into_log_events
from app.services.mongo.projects import (
    add_project_events,
    collect_languages,
    delete_project_from_id,
    delete_project_related_resources,
    email_project_data,
    get_project_by_id,
    update_project,
)

from app.services.mongo.tasks import get_all_tasks
from app.services.mongo.sessions import get_all_sessions
from app.services.mongo.users import fetch_users_metadata, get_nb_users_messages
from app.services.slack import slack_notification
from app.services.universal_loader.universal_loader import universal_loader
from app.utils import cast_datetime_or_timestamp_to_timestamp

router = APIRouter(tags=["Projects"])


@router.get(
    "/projects/{project_id}",
    response_model=Project,
    description="Get a specific project",
)
async def get_project(
    project_id: str,
    user: User = Depends(propelauth.require_user),
) -> Project:
    """
    Get a specific project
    """
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)
    return project


@router.delete(
    "/projects/{project_id}/delete",
    response_model=None,
    description="Delete a project",
)
async def delete_project(
    project_id: str,
    background_tasks: BackgroundTasks,
    cascade_delete: bool = False,
    user: User = Depends(propelauth.require_user),
) -> Project:
    """
    Delete a project. Pass cascade_delete=True to delete all the related resources (sessions, events, tasks, tests).
    """
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)

    await delete_project_from_id(project_id=project_id)

    # If cascade, delete all the related resources
    if cascade_delete:
        background_tasks.add_task(
            delete_project_related_resources, project_id=project_id
        )

    return project


@router.post(
    "/projects/{project_id}",
    response_model=Project,
    description="Update a project. Only the fields that are specified in the request will be updated. Specified fields will be overwritten (WARNING for nested fields like settings))",
)
async def post_update_project(
    project_id: str,
    project_update_request: ProjectUpdateRequest,
    user: User = Depends(propelauth.require_user),
) -> Project:
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)
    updated_project = await update_project(
        project, **project_update_request.model_dump()
    )
    return updated_project


@router.post(
    "/projects/{project_id}/sessions",
    response_model=Sessions,
    description="Get all the sessions of a project",
)
async def post_sessions(
    project_id: str,
    query: Optional[QuerySessionsTasksRequest] = None,
    user: User = Depends(propelauth.require_user),
) -> Sessions:
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)
    if query is None:
        query = QuerySessionsTasksRequest()
    # Convert to UNIX timestamp in seconds
    if isinstance(query.filters.created_at_start, datetime.datetime):
        query.filters.created_at_start = int(query.filters.created_at_start.timestamp())
    if isinstance(query.filters.created_at_end, datetime.datetime):
        query.filters.created_at_end = int(query.filters.created_at_end.timestamp())

    sessions = await get_all_sessions(
        project_id=project_id,
        get_events=True,
        get_tasks=False,
        filters=query.filters,
        pagination=query.pagination,
        sorting=query.sorting,
    )
    return Sessions(sessions=sessions)


@router.get(
    "/projects/{project_id}/sessions",
    response_model=Sessions,
    description="Get all the sessions of a project",
)
async def get_sessions(
    project_id: str,
    user: User = Depends(propelauth.require_user),
) -> Sessions:
    return await post_sessions(project_id=project_id, user=user)


@router.get(
    "/projects/{project_id}/events",
    response_model=Events,
    description="Get all the events of a project",
)
async def get_events(
    project_id: str,
    limit: int = 1000,
    user: User = Depends(propelauth.require_user),
) -> Events:
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)
    events = await get_all_events(project_id=project_id, limit=limit)
    return Events(events=events)


@router.get(
    "/projects/{project_id}/languages",
    description="Get the list of all unique languages detected in a project.",
    response_model=List[str],
)
async def get_languages(
    project_id: str,
    user: User = Depends(propelauth.require_user),
) -> List[str]:
    """
    Get the list of all unique languages detected in a project.
    """
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)
    languages = await collect_languages(project_id=project_id)
    return languages


@router.post(
    "/projects/{project_id}/tasks",
    response_model=Tasks,
    description="Fetch all the tasks of a project",
)
async def post_tasks(
    project_id: str,
    query: Optional[QuerySessionsTasksRequest] = None,
    user: User = Depends(propelauth.require_user),
):
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)

    if query is None:
        query = QuerySessionsTasksRequest()
    if query.filters.user_id is not None:
        if query.filters.metadata is None:
            query.filters.metadata = {}
        query.filters.metadata["user_id"] = query.filters.user_id

    tasks = await get_all_tasks(
        project_id=project_id,
        limit=None,
        validate_metadata=True,
        filters=query.filters,
        sorting=query.sorting,
        pagination=query.pagination,
    )
    return Tasks(tasks=tasks)


@router.get(
    "/projects/{project_id}/tasks",
    response_model=Tasks,
    description="Get all the tasks of a project",
)
async def get_tasks(
    project_id: str,
    user: User = Depends(propelauth.require_user),
):
    return await post_tasks(project_id=project_id, user=user)


@router.get(
    "/projects/{project_id}/tasks/email",
    description="Get an email with the tasks of a project in csv and xlsx format",
)
async def email_tasks(
    project_id: str,
    background_tasks: BackgroundTasks,
    user: User = Depends(propelauth.require_user),
) -> dict:
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)
    # Trigger the email sending in the background
    background_tasks.add_task(
        email_project_data, project_id=project_id, uid=user.user_id, scope="tasks"
    )
    logger.info(f"Emailing tasks of project {project_id} to {user.email}")
    return {"status": "ok"}


@router.post(
    "/projects/{project_id}/users/email",
    description="Get an email with the users data of a project in csv and xlsx format",
)
async def email_users(
    project_id: str,
    query: EmailUsersQuery,
    background_tasks: BackgroundTasks,
    user: User = Depends(propelauth.require_user),
) -> dict:
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)

    nb_users = await get_nb_users_messages(project_id=project_id, filters=query.filters)
    logger.info(f"Number of users in project {project_id}: {nb_users}")

    if nb_users is None or nb_users == 0:
        return {
            "exception_empty_data": "exception_data_empty",
            "message": "No users found in the project.",
        }
    # Trigger the email sending in the background
    background_tasks.add_task(
        email_project_data,
        project_id=project_id,
        filters=query.filters,
        uid=user.user_id,
        scope="users",
    )
    logger.info(f"Emailing users of project {project_id} to {user.email}")
    return {"status": "ok"}


@router.post(
    "/projects/{project_id}/add-events",
    response_model=Project,
    description="Add events to a project",
)
async def add_events(
    project_id: str,
    events: AddEventsQuery,
    user: User = Depends(propelauth.require_user),
) -> Project:
    """
    Add events to a project
    """
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)
    # Add events to the project
    logger.debug(f"Adding events to project {project_id}: {events.events}")
    updated_project = await add_project_events(project_id, events.events)
    return updated_project


@router.post(
    "/projects/{project_id}/users",
    response_model=Users,
    description="Get all the metadata about the end-users of a project",
)
async def get_users(
    project_id: str,
    query: QueryUserMetadataRequest,
    user: User = Depends(propelauth.require_user),
) -> Users:
    """
    Get metadata about the end-users of a project
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)

    filters = query.filters
    if isinstance(filters.created_at_start, datetime.datetime):
        filters.created_at_start = cast_datetime_or_timestamp_to_timestamp(
            filters.created_at_start
        )
    if isinstance(filters.created_at_end, datetime.datetime):
        filters.created_at_end = cast_datetime_or_timestamp_to_timestamp(
            filters.created_at_end
        )

    if query.sorting is None:
        query.sorting = [
            Sorting(id="last_message_ts", desc=True),
            Sorting(id="user_id", desc=True),
        ]
    else:
        # Always resort by user_id to ensure the same order
        # when multiple users have the same last_timestamp_ts or values
        query.sorting.append(Sorting(id="user_id", desc=True))

    users = await fetch_users_metadata(
        project_id=project_id,
        filters=filters,
        sorting=query.sorting,
        pagination=query.pagination,
        user_id_search=query.user_id_search,
    )
    return Users(users=users)


@router.get(
    "/projects/{project_id}/unique-events",
    response_model=Events,
)
async def get_project_unique_events(
    project_id: str,
    filters: Optional[ProjectDataFilters] = None,
    user: User = Depends(propelauth.require_user),
) -> Events:
    """
    Get the unique observed events in a project
    """
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)
    events = await get_all_events(
        project_id=project_id,
        filters=filters,
        include_removed=True,
        unique=True,
    )
    return Events(events=events)


@router.post(
    "/projects/{project_id}/upload-tasks",
    response_model=dict,
)
async def post_upload_tasks(
    project_id: str,
    file: UploadFile,
    # file_params: UploadTasksRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(propelauth.require_user),
) -> dict:
    """
    Upload a file with tasks to a project

    Supported file formats: csv, xlsx, parquet, jsonl

    The file should contain the following columns:
    - input: the input text
    - output: the expected output text

    Optional columns:
    - task_id: the task id
    - session_id: the session id to which the task is associated
    - user_id: the user id who created the task
    - created_at: the creation date of the task
    """
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)

    if not file.filename:
        raise HTTPException(status_code=400, detail="Error: No file provided.")

    SUPPORTED_EXTENSIONS = [
        "csv",
        "xlsx",
        "jsonl",
        "parquet",
    ]  # Add the supported extensions here
    file_extension = file.filename.split(".")[-1]
    if file_extension not in SUPPORTED_EXTENSIONS:
        # We send a slack notification to the phospho team
        await slack_notification(
            f"Project {project_id} uploaded a file with unsupported extension {file_extension}"
        )
        raise HTTPException(
            status_code=400,
            detail=f"Error: The extension {file_extension} is not supported (supported: {SUPPORTED_EXTENSIONS}).",
        )

    # Push the file to a GCP bucket named "platform-import-data"
    if config.GCP_BUCKET_CLIENT:
        timestamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
        filepath = f"{project.org_id}/{project_id}/{timestamp}_{file.filename}"
        logger.info(f"Uploading file {file.filename} to GCP bucket as {filepath}")

        bucket = Bucket(client=config.GCP_BUCKET_CLIENT, name="platform-import-data")
        blob = bucket.blob(filepath)
        blob.upload_from_file(file.file)
        # Reset the file pointer to the start
        file.file.seek(0)

    # Read file content -> into memory
    file_params: dict = {}
    logger.info(f"Reading file {file.filename} content.")
    tasks_df: pd.DataFrame
    try:
        if file_extension == "csv":
            tasks_df = pd.read_csv(
                file.file, sep=None, engine="python", on_bad_lines="warn", **file_params
            )
        elif file_extension == "xlsx":
            tasks_df = pd.read_excel(file.file, **file_params)
        elif file_extension == "jsonl":
            tasks_df = pd.read_json(file.file, lines=True)
        elif file_extension == "parquet":
            tasks_df = pd.read_parquet(file.file)
            logger.debug(f"tasks_df: {tasks_df}")
        else:
            # This only happens if you add a new extension and forget to update the supported extensions list
            raise NotImplementedError(
                f"Error: The extension {file_extension} is not supported (supported: {SUPPORTED_EXTENSIONS})."
            )
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error: Could not read the file content. {e}"
        )

    # Strip and lowercase the columns
    tasks_df.columns = tasks_df.columns.str.strip().str.lower()
    logger.debug(f"Columns: {list(tasks_df.columns)}")

    # strip and lowercase the columns
    tasks_df.columns = (
        tasks_df.columns.str.strip().str.lower().str.replace("\ufeff", "")  # Remove BOM
    )
    # Rename task_input to input and task_output to output
    tasks_df.rename(
        columns={
            "task_input": "input",
            "task_output": "output",
            "task_created_at": "created_at",
        },
        inplace=True,
    )

    new_tasks_df = await universal_loader(tasks_df)

    if new_tasks_df is None:
        # The file has been uploaded but the columns are missing (wrong format)
        # We send a slack notification to the phospho team for manual verification
        if config.GCP_BUCKET_CLIENT:
            # Otherwise filepath is undefined, see above
            await slack_notification(
                f"[ACTION REQUIRED] {user.email} project {project_id} uploaded a file with missing columns. File path: {filepath}"
            )

        raise HTTPException(
            status_code=400,
            # Display to the user the delayed processing
            # It is displayed in a toast message in the frontend
            detail="Missing columns. We will process your file manually in the next 24 hours.",
        )

    # Check if 'task_id' column exists and contains unique values

    if "task_id" in new_tasks_df.columns:
        if new_tasks_df["task_id"].nunique() != len(new_tasks_df["task_id"]):
            # raise HTTPException(
            #     status_code=400,
            #     detail="Error: The 'task_id' column contains duplicate values. Each task_id must be unique.",
            # )
            # Drop duplicates to only keep the first occurence
            new_tasks_df.drop_duplicates(subset=["task_id"], keep="first", inplace=True)

    # Drop rows with missing column "input"
    old_len = new_tasks_df.shape[0]
    new_tasks_df.dropna(subset=["input"], inplace=True)
    new_len = new_tasks_df.shape[0]

    # Process the csv file as a background task
    logger.info(f"File {file.filename} uploaded successfully. Processing tasks.")
    background_tasks.add_task(
        process_file_upload_into_log_events,
        tasks_df=new_tasks_df,
        project_id=project_id,
        org_id=project.org_id,
    )
    return {
        "status": "ok",
        "nb_rows_processed": new_tasks_df.shape[0],
        "nb_rows_dropped": old_len - new_len,
    }


@router.post(
    "/projects/{project_id}/connect-langsmith",
    response_model=dict,
)
async def connect_langsmith(
    project_id: str,
    query: ConnectLangsmithQuery,
    background_tasks: BackgroundTasks,
    user: User = Depends(propelauth.require_user),
) -> dict:
    """
    Import data from Langsmith to a Phospho project
    """
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)

    logger.debug(f"Connecting Langsmith to project {project_id}")

    try:
        # This snippet is used to test the connection with Langsmith and verify the API key/project name
        from langsmith import Client

        client = Client(api_key=query.langsmith_api_key)
        runs = client.list_runs(
            project_name=query.langsmith_project_name,
            start_time=datetime.datetime.now() - datetime.timedelta(seconds=1),
        )
        _ = [run for run in runs]
    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error: Could not connect to Langsmith: {e}"
        )

    usage_quota = await get_quota(project_id)

    extractor_client = ExtractorClient(
        project_id=project_id,
        org_id=project.org_id,
    )
    background_tasks.add_task(
        extractor_client.collect_langsmith_data,
        langsmith_api_key=query.langsmith_api_key,
        langsmith_project_name=query.langsmith_project_name,
        current_usage=usage_quota.current_usage,
        max_usage=usage_quota.max_usage,
    )
    return {"status": "ok", "message": "Langsmith connected successfully."}


@router.post(
    "/projects/{project_id}/connect-langfuse",
    response_model=dict,
)
async def connect_langfuse(
    project_id: str,
    query: ConnectLangfuseQuery,
    background_tasks: BackgroundTasks,
    user: User = Depends(propelauth.require_user),
) -> dict:
    """
    Import data from Langfuse to a Phospho project
    """
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)

    logger.debug(f"Connecting LangFuse to project {project_id}")

    try:
        langfuse = Langfuse(
            public_key=query.langfuse_public_key,
            secret_key=query.langfuse_secret_key,
            host="https://cloud.langfuse.com",
        )
        langfuse.auth_check()
        langfuse.shutdown()
        logger.debug("LangFuse connected successfully.")

    except Exception as e:
        raise HTTPException(
            status_code=400, detail=f"Error: Could not connect to LangFuse: {e}"
        )

    usage_quota = await get_quota(project_id)

    extractor_client = ExtractorClient(
        project_id=project_id,
        org_id=project.org_id,
    )
    background_tasks.add_task(
        extractor_client.collect_langfuse_data,
        langfuse_secret_key=query.langfuse_secret_key,
        langfuse_public_key=query.langfuse_public_key,
        current_usage=usage_quota.current_usage,
        max_usage=usage_quota.max_usage,
    )
    return {"status": "ok", "message": "LangFuse connected successfully."}
