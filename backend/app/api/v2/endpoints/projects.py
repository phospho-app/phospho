from typing import Optional

from fastapi import APIRouter, Depends

from app.api.v2.models import ProjectTasksFilter, Sessions, Tasks

# from app.db.client import firestore_db as firestore_db
from app.security import authenticate_org_key, verify_propelauth_org_owns_project_id
from app.services.mongo.projects import get_all_sessions, get_all_tasks

router = APIRouter(tags=["Projects"])


@router.get(
    "/projects/{project_id}/sessions",
    response_model=Sessions,
    description="Get all the sessions of a project",
)
async def get_sessions(
    project_id: str,
    limit: int = 1000,
    org: dict = Depends(authenticate_org_key),
):
    await verify_propelauth_org_owns_project_id(org, project_id)
    sessions = await get_all_sessions(project_id, limit)
    return Sessions(sessions=sessions)


@router.get(
    "/projects/{project_id}/tasks",
    response_model=Tasks,
    description="Get all the tasks of a project",
)
async def get_tasks(
    project_id: str,
    limit: int = 1000,
    task_filter: Optional[ProjectTasksFilter] = None,
    org: dict = Depends(authenticate_org_key),
) -> Tasks:
    """
    Get all the tasks of a project. If task_filter is specified, the tasks will be filtered according to the filter.

    Args:
        project_id: The id of the project
        limit: The maximum number of tasks to return
        task_filter: This model is used to filter tasks in the get_tasks endpoint. The filters are applied as AND filters.
    """
    await verify_propelauth_org_owns_project_id(org, project_id)
    if task_filter is None:
        task_filter = ProjectTasksFilter()
    if isinstance(task_filter.event_name, str):
        task_filter.event_name = [task_filter.event_name]

    tasks = await get_all_tasks(
        project_id=project_id,
        limit=limit,
        flag_filter=task_filter.flag,
        event_name_filter=task_filter.event_name,
        last_eval_source_filter=task_filter.last_eval_source,
        metadata_filter=task_filter.metadata,
    )
    return Tasks(tasks=tasks)
