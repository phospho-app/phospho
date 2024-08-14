from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from loguru import logger

from app.api.v2.models import (
    AnalyticsQueryRequest,
    AnalyticsQueryResponse,
    ComputeJobsRequest,
    FlattenedTasks,
    FlattenedTasksRequest,
    QuerySessionsTasksRequest,
    Sessions,
    Tasks,
)
from app.db.models import AnalyticsQuery
from app.security import authenticate_org_key, verify_propelauth_org_owns_project_id
from app.services.mongo.explore import (
    fetch_flattened_tasks,
    update_from_flattened_tasks,
    run_analytics_query,
    analytics_query_result_to_timeseries,
)
from app.services.mongo.projects import (
    backcompute_recipes,
    get_all_sessions,
)
from app.services.mongo.tasks import get_all_tasks
from phospho.models import AnalyticsQueryFilters

from app.utils import generate_timestamp

router = APIRouter(tags=["Projects"])


@router.post(
    "/projects/{project_id}/sessions",
    response_model=Sessions,
    description="Fetch all the sessions of a project",
)
async def get_sessions(
    project_id: str,
    limit: int = 1000,
    org: dict = Depends(authenticate_org_key),
):
    await verify_propelauth_org_owns_project_id(org, project_id)
    sessions = await get_all_sessions(project_id, limit)
    return Sessions(sessions=sessions)


@router.post(
    "/projects/{project_id}/tasks",
    response_model=Tasks,
    description="Fetch all the tasks of a project",
)
async def post_tasks(
    project_id: str,
    query: Optional[QuerySessionsTasksRequest] = None,
    org: dict = Depends(authenticate_org_key),
) -> Tasks:
    """
    Fetch all the tasks of a project.

    The filters are combined as AND conditions on the different fields.
    """
    await verify_propelauth_org_owns_project_id(org, project_id)
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
    )
    return Tasks(tasks=tasks)


@router.post(
    "/projects/{project_id}/tasks/flat",
    response_model=FlattenedTasks,
    description="Get all the tasks of a project",
)
async def get_flattened_tasks(
    project_id: str,
    flattened_tasks_request: FlattenedTasksRequest,
    org: dict = Depends(authenticate_org_key),
) -> FlattenedTasks:
    """
    Get all the tasks of a project in a flattened format.
    """
    await verify_propelauth_org_owns_project_id(org, project_id)

    flattened_tasks = await fetch_flattened_tasks(
        project_id=project_id,
        limit=flattened_tasks_request.limit,
        with_events=flattened_tasks_request.with_events,
        with_sessions=flattened_tasks_request.with_sessions,
        with_removed_events=flattened_tasks_request.with_removed_events,
    )
    return FlattenedTasks(flattened_tasks=flattened_tasks)


@router.post(
    "/projects/{project_id}/tasks/flat-update",
    description="Update the tasks of a project using a flattened format",
)
async def post_flattened_tasks(
    project_id: str,
    flattened_tasks: FlattenedTasks,
    org: dict = Depends(authenticate_org_key),
) -> None:
    """
    Update the tasks of a project using a flattened format.
    """
    await verify_propelauth_org_owns_project_id(org, project_id)
    org_id = org["org"].get("org_id")

    await update_from_flattened_tasks(
        org_id=org_id,
        project_id=project_id,
        flattened_tasks=flattened_tasks.flattened_tasks,
    )
    return None


@router.post(
    "/projects/{project_id}/compute-jobs",
    description="Run predictions for a list of jobs on all the tasks of a project matching a filter and that have not been processed yet",
)
async def post_backcompute_job(
    background_tasks: BackgroundTasks,
    project_id: str,
    compute_job_request: ComputeJobsRequest,
    limit: int = 10000,
    org: dict = Depends(authenticate_org_key),
):
    """
    Run predictions for a job on all the tasks of a project that have not been processed yet.
    """
    await verify_propelauth_org_owns_project_id(org, project_id)

    # Limit the number of tasks to process
    HARD_LIMIT = 1000
    limit = min(limit, HARD_LIMIT)

    # Limit the number of jobs to run
    NB_JOBS_LIMIT = 10
    if len(compute_job_request.job_ids) > NB_JOBS_LIMIT:
        logger.warning(
            f"Number of jobs {len(compute_job_request.job_ids)} is greater than the limit {NB_JOBS_LIMIT}, only the first {NB_JOBS_LIMIT} jobs will be processed"
        )

    job_ids = compute_job_request.job_ids[:NB_JOBS_LIMIT]

    background_tasks.add_task(
        backcompute_recipes,
        project_id,
        job_ids,
        compute_job_request.filters,
        limit=limit,
    )

    return {"message": "Backcompute job started"}


@router.post(
    "/projects/{project_id}/query",
    description="Run a query on the project",
    response_model=AnalyticsQueryResponse,
)
async def post_run_query(
    project_id: str,
    analytics_query_request: AnalyticsQuery,
    org: dict = Depends(authenticate_org_key),
):
    """
    Run a query on the project.
    The main purpose of this endpoint is to enable customers:
    - to build their own analytics on top of the data produced by phospho (white label)
    - to run custom queries on the data for data science purposes

    Result max size is limited to config.QUERY_MAX_LEN_LIMIT rows.
    """
    await verify_propelauth_org_owns_project_id(org, project_id)
    if analytics_query_request.project_id != project_id:
        raise HTTPException(
            status_code=403,
            detail="The project_id in the query does not match the project_id in the URL",
        )
    # Add checks on the query here
    # ...

    # Run the query
    query_result = await run_analytics_query(analytics_query_request)

    # # Fill missing times
    # filled_result = analytic_query_result_fill_missing_times(
    #     query_result, "hour", generate_timestamp() - 24 * 3600, generate_timestamp()
    # )
    end_timestamp = generate_timestamp()
    if analytics_query_request.filters.created_at_end is not None:
        end_timestamp = analytics_query_request.filters.created_at_end
    result = analytics_query_result_to_timeseries(
        query_result,
        "day",
        analytics_query_request.filters.created_at_start,
        end_timestamp,
    )

    return AnalyticsQueryResponse(result=result)
