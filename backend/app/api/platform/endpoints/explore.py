import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from propelauth_fastapi import User

from app.api.platform.models import (
    AggregateMetricsRequest,
    ProjectDataFilters,
    Events,
    Tasks,
    ABTests,
    Topics,
    EventsMetricsFilter,
    DashboardMetricsFilter,
)
from app.security.authentification import propelauth
from app.security import verify_if_propelauth_user_can_access_project
from app.services.mongo.explore import (
    deprecated_get_dashboard_aggregated_metrics,
    get_sessions_aggregated_metrics,
    get_tasks_aggregated_metrics,
    get_events_aggregated_metrics,
    project_has_tasks,
    project_has_sessions,
    project_has_enough_labelled_tasks,
    create_ab_tests_table,
    fetch_topics,
    nb_items_with_a_metadata_field,
    compute_nb_items_with_metadata_field,
    compute_session_length_per_metadata,
    compute_successrate_metadata_quantiles,
    get_dashboard_aggregated_metrics,
)
from app.services.mongo.projects import get_all_events, get_all_tasks
from app.core import config


router = APIRouter(tags=["Explore"])


@router.post(
    "/explore/{project_id}/has-tasks",
    description="Check if a project has tasks. Used to nudge the user to create tasks.",
)
async def post_project_has_tasks(
    project_id: str,
    user: User = Depends(propelauth.require_user),
) -> dict:
    """
    Check if a project has tasks. If not, display a tutorial to the user.
    Should be super fast.
    """
    if not project_id:
        raise HTTPException(
            status_code=400,
            detail="Missing project_id in request.",
        )
    await verify_if_propelauth_user_can_access_project(user, project_id)
    has_tasks = await project_has_tasks(project_id=project_id)
    if not has_tasks:
        logger.info(f"Project {project_id} has no tasks (user: {user.email})")
    return {"has_tasks": has_tasks}


@router.post(
    "/explore/{project_id}/has-sessions",
    description="Check if a project has sessions. Used to nudge the user to create sessions.",
)
async def post_project_has_sessions(
    project_id: str,
    user: User = Depends(propelauth.require_user),
) -> dict:
    """
    Check if a project has sessions. If not, display a tutorial to the user.
    Should be super fast.
    """
    if not project_id:
        raise HTTPException(
            status_code=400,
            detail="Missing project_id in request.",
        )
    await verify_if_propelauth_user_can_access_project(user, project_id)
    has_sessions = await project_has_sessions(project_id=project_id)
    if not has_sessions:
        logger.info(f"Project {project_id} has no sessions (user: {user.email})")
    return {"has_sessions": has_sessions}


@router.post(
    "/explore/{project_id}/has-enough-labelled-tasks",
    description="Check if a project has labelled tasks. Used to nudge the user to label tasks.",
)
async def post_project_has_enough_labelled_tasks(
    project_id: str,
    user: User = Depends(propelauth.require_user),
) -> dict:
    """
    Check if a project has labelled tasks. If not, display a tutorial to the user.
    Should be super fast.
    """
    if not project_id:
        raise HTTPException(
            status_code=400,
            detail="Missing project_id in request.",
        )
    await verify_if_propelauth_user_can_access_project(user, project_id)
    # The number of labelled tasks to consider the project as having enough labelled tasks
    enough = config.FEW_SHOT_MIN_NUMBER_OF_EXAMPLES
    currently_labelled_tasks = await project_has_enough_labelled_tasks(
        project_id=project_id, enough=enough
    )
    logger.info(
        f"Project {project_id} has {currently_labelled_tasks}/{enough} labelled tasks (user: {user.email})"
    )
    return {
        "project_id": project_id,
        "enough_labelled_tasks": enough,
        "has_enough_labelled_tasks": bool(currently_labelled_tasks >= enough),
        "currently_labelled_tasks": currently_labelled_tasks,
    }


@router.post(
    "/explore/{project_id}/aggregated",
    description="Get aggregated metrics for a project. Used for the main dashboard.",
)
async def get_dashboard_project_metrics(
    project_id: str,
    request: AggregateMetricsRequest,
    user: User = Depends(propelauth.require_user),
) -> List[dict]:
    """
    Get aggregated metrics for a project. Used for dashboard.
    """
    logger.info(f"Dashboard request: {request.model_dump()}")
    await verify_if_propelauth_user_can_access_project(user, project_id)

    output = await deprecated_get_dashboard_aggregated_metrics(
        project_id=project_id,
        limit=request.limit,
        index=request.index,
        columns=request.columns,
        count_of=request.count_of,
        timerange=request.timerange,
        filters=request.filters,
    )
    return output


@router.post(
    "/explore/{project_id}/aggregated/tasks",
    description="Get aggregated metrics for the tasks of a project. Used for the Tasks dashboard.",
)
async def get_tasks_project_metrics(
    project_id: str,
    metrics: Optional[List[str]] = None,
    tasks_filter: Optional[ProjectDataFilters] = None,
    user: User = Depends(propelauth.require_user),
) -> dict:
    """
    Get aggregated metrics for the tasks of a project. Used for the Tasks dashboard.
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)
    logger.info(f"Tasks request: {tasks_filter}")
    if tasks_filter is None:
        tasks_filter = ProjectDataFilters(flag=None, event_name=None)
    if isinstance(tasks_filter.event_name, str):
        tasks_filter.event_name = [tasks_filter.event_name]
    # Convert to UNIX timestamp in seconds
    if isinstance(tasks_filter.created_at_start, datetime.datetime):
        tasks_filter.created_at_start = int(tasks_filter.created_at_start.timestamp())
    if isinstance(tasks_filter.created_at_end, datetime.datetime):
        tasks_filter.created_at_end = int(tasks_filter.created_at_end.timestamp())

    output = await get_tasks_aggregated_metrics(
        project_id=project_id,
        flag_filter=tasks_filter.flag,
        event_name_filter=tasks_filter.event_name,
        metrics=metrics,
        created_at_start=tasks_filter.created_at_start,
        created_at_end=tasks_filter.created_at_end,
    )
    return output


@router.post(
    "/explore/{project_id}/aggregated/sessions",
    description="Get aggregated metrics for the sessions of a project. Used for the Sessions dashboard.",
)
async def get_sessions_project_metrics(
    project_id: str,
    metrics: Optional[List[str]] = None,
    sessions_filter: Optional[ProjectDataFilters] = None,
    user: User = Depends(propelauth.require_user),
) -> dict:
    """
    Get aggregated metrics for the sessions of a project. Used for the Sessions dashboard.
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)
    logger.info(f"Sessions request: {sessions_filter}")
    if sessions_filter is None:
        sessions_filter = ProjectDataFilters(event_name=None)
    if isinstance(sessions_filter.event_name, str):
        sessions_filter.event_name = [sessions_filter.event_name]
    # Convert to UNIX timestamp in seconds
    if isinstance(sessions_filter.created_at_start, datetime.datetime):
        sessions_filter.created_at_start = int(
            sessions_filter.created_at_start.timestamp()
        )
    if isinstance(sessions_filter.created_at_end, datetime.datetime):
        sessions_filter.created_at_end = int(sessions_filter.created_at_end.timestamp())

    output = await get_sessions_aggregated_metrics(
        project_id=project_id,
        metrics=metrics,
        event_name_filter=sessions_filter.event_name,
        created_at_start=sessions_filter.created_at_start,
        created_at_end=sessions_filter.created_at_end,
    )
    return output


@router.post(
    "/explore/{project_id}/aggregated/events",
    description="Get aggregated metrics for the events of a project. Used for the Events dashboard.",
)
async def get_events_project_metrics(
    project_id: str,
    metrics: Optional[List[str]] = None,
    events_filter: Optional[EventsMetricsFilter] = None,
    user: User = Depends(propelauth.require_user),
):
    """
    Get aggregated metrics for the events of a project. Used for the Events dashboard.
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)
    output = await get_events_aggregated_metrics(
        project_id=project_id,
        metrics=metrics,
    )
    return output


@router.post(
    "/explore/{project_id}/events",
    response_model=Events,
    description="Get the events of a project that match the filter",
)
async def get_filtered_events(
    project_id: str,
    limit: int = 1000,
    events_filter: Optional[ProjectDataFilters] = None,
    user: User = Depends(propelauth.require_user),
) -> Events:
    await verify_if_propelauth_user_can_access_project(user, project_id)

    events = await get_all_events(
        project_id=project_id, limit=limit, events_filter=events_filter
    )
    return Events(events=events)


@router.get(
    "/explore/{project_id}/ab-tests",
    response_model=ABTests,
    description="Get the different scores of the ab tests of a project",
)
async def get_ab_tests(
    project_id: str,
    limit: int = 10000,
    user: User = Depends(propelauth.require_user),
) -> ABTests:
    """
    Get the different scores of the ab tests of a project.

    AB tests are tasks with a version_id. The version_id is used to group the tasks together.
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)
    ab_tests = await create_ab_tests_table(project_id=project_id, limit=limit)
    return ABTests(abtests=ab_tests)


@router.get(
    "/explore/{project_id}/topics",
    response_model=Topics,
    description="Get the different topics of a project",
)
async def get_topics(
    project_id: str,
    user: User = Depends(propelauth.require_user),
) -> Topics:
    """
    Get the different topics of a project.

    Topics are labels that can be assigned to tasks.
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)

    topics = await fetch_topics(project_id=project_id)

    logger.debug(f"Topics: {topics}")

    return topics


@router.get(
    "/explore/{project_id}/nb_items_with_a_metadata_field/{collection_name}/{metadata_field}",
    description="Get the number of different metadata values in a project.",
)
async def get_nb_items_with_a_metadata_field(
    project_id: str,
    collection_name: str,
    metadata_field: str,
    user: User = Depends(propelauth.require_user),
) -> dict:
    await verify_if_propelauth_user_can_access_project(user, project_id)

    count = await nb_items_with_a_metadata_field(
        project_id=project_id,
        collection_name=collection_name,
        metadata_field=metadata_field,
    )

    return {"value": count}


@router.get(
    "/explore/{project_id}/compute_nb_items_with_metadata_field/{collection_name}/{metadata_field}",
    description="Get the average number of metadata values in a project.",
)
async def get_compute_nb_items_with_metadata_field(
    project_id: str,
    collection_name: str,
    metadata_field: str,
    user: User = Depends(propelauth.require_user),
) -> dict:
    await verify_if_propelauth_user_can_access_project(user, project_id)

    quantile_value = 0.1

    (
        bottom_quantile,
        average,
        top_quantile,
    ) = await compute_nb_items_with_metadata_field(
        project_id=project_id,
        collection_name=collection_name,
        metadata_field=metadata_field,
        quantile_value=quantile_value,
    )

    return {
        "bottom_quantile": bottom_quantile,
        "average": average,
        "top_quantile": top_quantile,
        "quantile_value": quantile_value,
    }


@router.get(
    "/explore/{project_id}/compute_session_length_per_metadata/{metadata_field}",
    description="Get the average session length for a metadata field.",
)
async def get_compute_session_length_per_metadata(
    project_id: str,
    metadata_field: str,
    user: User = Depends(propelauth.require_user),
) -> dict:
    await verify_if_propelauth_user_can_access_project(user, project_id)

    quantile_value = 0.1

    (
        bottom_quantile,
        average,
        top_quantile,
    ) = await compute_session_length_per_metadata(
        project_id=project_id,
        metadata_field=metadata_field,
        quantile_value=quantile_value,
    )

    return {
        "bottom_quantile": bottom_quantile,
        "average": average,
        "top_quantile": top_quantile,
        "quantile_value": quantile_value,
    }


@router.get(
    "/metadata/{project_id}/successrate-stats/{collection_name}/{metdata_field}",
    description="Get the stats on success rate for a project's collection.",
)
async def get_successrate_stats(
    project_id: str,
    collection_name: str,
    metadata_field: str,
    user: User = Depends(propelauth.require_user),
) -> dict:
    await verify_if_propelauth_user_can_access_project(user, project_id)

    (
        bottom_quantile,
        average,
        top_quantile,
    ) = await compute_successrate_metadata_quantiles(
        project_id, metadata_field, collection_name=collection_name
    )

    return {
        "bottom_quantile": bottom_quantile,
        "average": average,
        "top_quantile": top_quantile,
    }


@router.post(
    "/explore/{project_id}/dashboard",
    description="Get the different graphs for the dashboard tab",
)
async def get_dashboard_graphs(
    project_id: str,
    metric: Optional[DashboardMetricsFilter] = None,
    user: User = Depends(propelauth.require_user),
):
    await verify_if_propelauth_user_can_access_project(user, project_id)
    if metric is None:
        metric = DashboardMetricsFilter()
    if metric.graph_name is None:
        metric.graph_name = []
    output = await get_dashboard_aggregated_metrics(
        project_id=project_id, metrics=metric.graph_name
    )
    return output
