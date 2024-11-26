import asyncio
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException

from phospho_backend.api.v2.models import (
    Task,
    TaskCreationRequest,
    TaskFlagRequest,
    TaskUpdateRequest,
    TaskHumanEvalRequest,
)
from phospho_backend.core import config
from phospho_backend.security.authentification import (
    authenticate_org_key,
    authenticate_org_key_no_exception,
    verify_propelauth_org_owns_project_id,
)
from phospho_backend.services.mongo.extractor import ExtractorClient
from phospho_backend.services.mongo.sessions import get_session_by_id
from phospho_backend.services.mongo.tasks import (
    create_task,
    get_task_by_id,
    update_task,
    human_eval_task,
)
from loguru import logger

router = APIRouter(tags=["Tasks"])


@router.post(
    "/tasks",
    response_model=Task,
    description="Create a new task",
)
async def post_create_task(
    taskCreationRequest: TaskCreationRequest,
    background_tasks: BackgroundTasks,
    org: dict = Depends(authenticate_org_key),
) -> Task:
    if taskCreationRequest.session_id is not None:
        session_data = await get_session_by_id(taskCreationRequest.session_id)
        await verify_propelauth_org_owns_project_id(org, session_data.project_id)
        project_id = session_data.project_id
    else:
        project_id = taskCreationRequest.project_id
        await verify_propelauth_org_owns_project_id(org, project_id)
    try:
        task_data = await create_task(
            project_id=project_id,
            session_id=taskCreationRequest.session_id,
            task_id=taskCreationRequest.task_id,
            input=taskCreationRequest.input,
            output=taskCreationRequest.output,
            additional_input=taskCreationRequest.additional_input,
            data=taskCreationRequest.data,
            org_id=org["org"].get("org_id"),
        )
        # Skip the pipeline if we are in test mode
        # This is because the background tasks hangs the test
        if config.ENVIRONMENT == "test" or config.MONGODB_NAME == "test":
            return task_data
        # Trigger the event detection pipeline asynchronously
        extractor_client = ExtractorClient(
            project_id=project_id,
            org_id=org["org"].get("org_id"),
        )
        background_tasks.add_task(
            extractor_client.run_main_pipeline_on_task, task=task_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to create task: {e}")
    return task_data


@router.get(
    "/tasks/{task_id}",
    response_model=Task,
    description="Get a specific task",
)
async def get_task(task_id: str, org: dict = Depends(authenticate_org_key)) -> Task:
    # Get the task object
    # WARNING : user not authorized at this point
    task = await get_task_by_id(task_id)
    await verify_propelauth_org_owns_project_id(org, task.project_id)
    return task


# This endpoint is only setup for compatibility with the phosphoJS client that uses the /tasks/{task_id}/flag endpoint
@router.post(
    "/tasks/{task_id}/flag",
    response_model=Task,
    description="Update the human rating of a task",
)
async def post_flag_task(
    task_id: str,
    taskFlagRequest: TaskFlagRequest,
    org: Optional[dict] = Depends(authenticate_org_key_no_exception),
) -> Task:
    """
    Set the human evalutation of the task to be 'success' or 'failure'
    Also adds a flag and signs the origin of the flag ("owner", "phospho", "user", etc.)
    """

    return await post_human_eval_task(
        task_id=task_id,
        taskHumanEvalRequest=TaskHumanEvalRequest(
            human_eval=taskFlagRequest.flag,
            source=taskFlagRequest.source,
            project_id=taskFlagRequest.project_id,
            notes=taskFlagRequest.notes,
        ),
        org=org,
    )


@router.post(
    "/tasks/{task_id}/human-eval",
    response_model=Task,
    description="Update the human rating of a task",
)
async def post_human_eval_task(
    task_id: str,
    taskHumanEvalRequest: TaskHumanEvalRequest,
    org: Optional[dict] = Depends(authenticate_org_key_no_exception),
) -> Task:
    """
    Set the human evalutation of the task to be 'success' or 'failure'
    Also adds a flag and signs the origin of the flag ("owner", "phospho", "user", etc.)
    """
    # Get the task object
    if taskHumanEvalRequest.human_eval not in ["success", "failure"]:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid flag value {taskHumanEvalRequest.human_eval}. Must be 'success' or 'failure'",
        )
    if taskHumanEvalRequest.project_id is None and org is None:
        raise HTTPException(
            status_code=400,
            detail="Please pass the project_id in the request body to flag the task.",
        )

    # The task may not exist yet, so we try to fetch it multiple times with exponential backoff
    delay = 1
    for _ in range(5):
        try:
            task_model = await get_task_by_id(task_id)
            break
        except Exception:
            logger.warning(f"Task {task_id} not found, retrying in {delay} seconds")
            await asyncio.sleep(delay)
            delay *= 2
    else:
        raise HTTPException(
            status_code=404,
            detail=f"Task {task_id} not found after multiple retries",
        )

    if org is not None:
        await verify_propelauth_org_owns_project_id(org, task_model.project_id)
    elif task_model.project_id != taskHumanEvalRequest.project_id:
        await asyncio.sleep(0.1)
        raise HTTPException(
            status_code=400,
            detail=f"Invalid project_id {taskHumanEvalRequest.project_id} for task {task_id}",
        )
    updated_task = await human_eval_task(
        task_model=task_model,
        human_eval=taskHumanEvalRequest.human_eval,
        source=taskHumanEvalRequest.source,
        notes=taskHumanEvalRequest.notes,
    )
    return updated_task


@router.post(
    "/tasks/{task_id}",
    response_model=Task,
    description="Update a task metadata",
)
async def post_update_task(
    task_id: str,
    taskUpdateRequest: TaskUpdateRequest,
    org: dict = Depends(authenticate_org_key),
) -> Task:
    """
    Edit the metadata of a task
    """
    # Get the task object
    task_model = await get_task_by_id(task_id)
    await verify_propelauth_org_owns_project_id(org, task_model.project_id)
    updated_task = await update_task(
        task_model=task_model,
        metadata=taskUpdateRequest.metadata,
        data=taskUpdateRequest.data,
        notes=taskUpdateRequest.notes,
        flag=taskUpdateRequest.flag,
        flag_source=taskUpdateRequest.flag_source,
    )
    return updated_task
