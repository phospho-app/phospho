from fastapi import APIRouter, Depends, HTTPException
from propelauth_fastapi import User

from app.api.platform.models import (
    Task,
    TaskFlagRequest,
    TaskUpdateRequest,
    AddEventRequest,
    RemoveEventRequest,
)
from app.security import verify_if_propelauth_user_can_access_project
from app.security.authentification import propelauth
from app.services.mongo.tasks import (
    flag_task,
    get_task_by_id,
    update_task,
    add_event_to_task,
    remove_event_from_task,
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
    description="Update a task",
)
async def post_update_task(
    task_id: str,
    taskUpdateRequest: TaskUpdateRequest,
    user: User = Depends(propelauth.require_user),
) -> Task:
    """
    Edit a logged task
    """
    task = await get_task_by_id(task_id)
    await verify_if_propelauth_user_can_access_project(user, task.project_id)

    updated_task = await update_task(
        task_model=task,
        **taskUpdateRequest.model_dump(),
    )
    return updated_task


@router.post(
    "/tasks/{task_id}/add-event",
    response_model=Task,
    description="Add an event to a task",
)
async def post_add_event_to_task(
    task_id: str,
    add_event: AddEventRequest,
    user: User = Depends(propelauth.require_user),
) -> Task:
    """
    Add an event to a task
    """
    task = await get_task_by_id(task_id)
    await verify_if_propelauth_user_can_access_project(user, task.project_id)

    updated_task = await add_event_to_task(
        task=task,
        event=add_event.event,
        score_range_value=add_event.score_range_value,
        score_category_label=add_event.score_category_label,
    )
    return updated_task


@router.post(
    "/tasks/{task_id}/remove-event",
    response_model=Task,
    description="Remove an event from a task",
)
async def post_remove_event_from_task(
    task_id: str,
    remove_event: RemoveEventRequest,
    user: User = Depends(propelauth.require_user),
) -> Task:
    """
    Remove an event from a task
    """
    task = await get_task_by_id(task_id)
    await verify_if_propelauth_user_can_access_project(user, task.project_id)

    updated_task = await remove_event_from_task(
        task=task,
        event_name=remove_event.event_name,
    )
    return updated_task
