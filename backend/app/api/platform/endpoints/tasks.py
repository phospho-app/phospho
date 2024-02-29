from fastapi import APIRouter, Depends, HTTPException
from propelauth_fastapi import User

from app.api.platform.models import (
    Task,
    TaskFlagRequest,
    TaskUpdateRequest,
)
from app.security import verify_if_propelauth_user_can_access_project
from app.security.authentification import propelauth
from app.services.mongo.tasks import (
    flag_task,
    get_task_by_id,
    update_task,
)

router = APIRouter(tags=["Tasks"])


@router.get(
    "/tasks/{task_id}",
    response_model=Task,
    description="Get a specific task",
)
async def get_task(task_id: str, user: User = Depends(propelauth.require_user)) -> Task:
    task = await get_task_by_id(task_id)
    await verify_if_propelauth_user_can_access_project(user, task.project_id)
    return task


@router.post(
    "/tasks/{task_id}/flag",
    response_model=Task,
    description="Update the status of a task",
)
async def post_flag_task(
    task_id: str,
    taskFlagRequest: TaskFlagRequest,
    user: User = Depends(propelauth.require_user),
) -> Task:
    """
    Set the flag of the task to be 'success' or 'failure'
    Sign the origin of the flag ("owner", "phospho", "user", etc.)
    """
    if taskFlagRequest.flag not in ["success", "failure"]:
        raise HTTPException(
            status_code=400,
            detail="The flag must be either 'success' or 'failure'",
        )
    task = await get_task_by_id(task_id)
    await verify_if_propelauth_user_can_access_project(user, task.project_id)
    updated_task = await flag_task(
        task_model=task,
        flag=taskFlagRequest.flag,
        source=taskFlagRequest.source,
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
    user: User = Depends(propelauth.require_user),
) -> Task:
    """
    Edit the metadata of a task
    """
    task = await get_task_by_id(task_id)
    await verify_if_propelauth_user_can_access_project(user, task.project_id)

    updated_task = await update_task(
        task_model=task,
        **taskUpdateRequest.model_dump(),
    )
    return updated_task
