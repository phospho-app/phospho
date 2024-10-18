import datetime
from typing import Dict, List, Optional, Union, cast

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from loguru import logger
from propelauth_fastapi import User  # type: ignore

from app.api.platform.models import (
    ABTests,
    AggregateMetricsRequest,
    Cluster,
    Clustering,
    ClusteringRequest,
    Clusterings,
    Clusters,
    DashboardMetricsFilter,
    DetectClustersRequest,
    Events,
    FetchClustersRequest,
    ProjectDataFilters,
    AggregatedSessionsRequest,
    ClusteringCostRequest,
)
from app.api.platform.models.explore import ABTestVersions, ClusteringEmbeddingCloud
from app.core import config
from app.security import verify_if_propelauth_user_can_access_project
from app.security.authentification import propelauth
from app.security.authorization import get_quota_for_org
from app.services.mongo.ai_hub import AIHubClient
from app.services.mongo.events import get_all_events, get_event_definition_from_event_id
from app.services.mongo.explore import (
    compute_cloud_of_clusters,
    create_ab_tests_table,
    deprecated_get_dashboard_aggregated_metrics,
    fetch_all_clusterings,
    fetch_all_clusters,
    fetch_single_cluster,
    get_ab_tests_versions,
    get_clustering_by_id,
    get_dashboard_aggregated_metrics,
    get_events_aggregated_metrics,
    get_nb_tasks_in_sessions,
    get_sessions_aggregated_metrics,
    get_tasks_aggregated_metrics,
    get_total_nb_of_sessions,
    project_has_enough_labelled_tasks,
    project_has_sessions,
    project_has_tasks,
)
from app.services.mongo.tasks import get_total_nb_of_tasks
from app.services.mongo.users import (
    get_nb_users_messages,
    get_users_aggregated_metrics,
    get_total_nb_of_users,
)
from app.utils import generate_uuid
from phospho.utils import generate_version_id

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
    enough = config.ANNOTATION_NUDGE_UNTIL_N_EXAMPLES
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
    filters: Optional[ProjectDataFilters] = None,
    user: User = Depends(propelauth.require_user),
) -> dict:
    """
    Get aggregated metrics for the tasks of a project. Used for the Tasks dashboard.
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)
    if filters is None:
        filters = ProjectDataFilters(flag=None, event_name=None)
    if isinstance(filters.event_name, str):
        filters.event_name = [filters.event_name]
    # Convert to UNIX timestamp in seconds
    if isinstance(filters.created_at_start, datetime.datetime):
        filters.created_at_start = int(filters.created_at_start.timestamp())
    if isinstance(filters.created_at_end, datetime.datetime):
        filters.created_at_end = int(filters.created_at_end.timestamp())

    output = await get_tasks_aggregated_metrics(
        project_id=project_id,
        metrics=metrics,
        filters=filters,
    )
    return output


@router.post(
    "/explore/{project_id}/aggregated/sessions",
    description="Get aggregated metrics for the sessions of a project. Used for the Sessions dashboard.",
)
async def get_sessions_project_metrics(
    project_id: str,
    query: AggregatedSessionsRequest,
    user: User = Depends(propelauth.require_user),
) -> dict:
    """
    Get aggregated metrics for the sessions of a project. Used for the Sessions dashboard.
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)
    metrics = query.metrics
    filters = query.filters
    limit = query.limit
    logger.debug(f"limit: {limit}")

    if isinstance(filters.event_name, str):
        filters.event_name = [filters.event_name]
    # Convert to UNIX timestamp in seconds
    if isinstance(filters.created_at_start, datetime.datetime):
        filters.created_at_start = int(filters.created_at_start.timestamp())
    if isinstance(filters.created_at_end, datetime.datetime):
        filters.created_at_end = int(filters.created_at_end.timestamp())

    output = await get_sessions_aggregated_metrics(
        project_id=project_id,
        metrics=metrics,
        filters=filters,
        limit=limit,
    )
    return output


@router.post(
    "/explore/{project_id}/clustering-cost",
    description="Aggregated statistics for running a clustering",
    response_model=dict,
)
async def get_project_metrics(
    project_id: str,
    query: ClusteringCostRequest,
    user: User = Depends(propelauth.require_user),
) -> dict:
    """
    Get aggregated metrics for the sessions of a project. Used for the Sessions dashboard.
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)
    filters = query.filters
    limit = query.limit

    # TODO : put all of this into a service

    if isinstance(filters.event_name, str):
        filters.event_name = [filters.event_name]
    # Convert to UNIX timestamp in seconds
    if isinstance(filters.created_at_start, datetime.datetime):
        filters.created_at_start = int(filters.created_at_start.timestamp())
    if isinstance(filters.created_at_end, datetime.datetime):
        filters.created_at_end = int(filters.created_at_end.timestamp())

    nb_elements: Optional[int] = None
    clustering_cost: Optional[int] = None
    output: Dict[str, Optional[float]] = {}
    logger.info(f"Clustering cost request: {query.model_dump()}")

    if query.scope == "sessions":
        total_nb_sessions = await get_total_nb_of_sessions(
            project_id=project_id,
            filters=filters,
        )
        nb_tasks_in_sessions = await get_nb_tasks_in_sessions(
            project_id=project_id,
            filters=filters,
            limit=limit,
        )
        output["total_nb_sessions"] = total_nb_sessions
        if limit is not None and total_nb_sessions is not None:
            output["nb_sessions_in_scope"] = min(total_nb_sessions, limit)
        else:
            output["nb_sessions_in_scope"] = total_nb_sessions
        output["nb_tasks_in_sessions"] = nb_tasks_in_sessions
        if nb_tasks_in_sessions is not None:
            nb_elements = nb_tasks_in_sessions

    elif query.scope == "messages":
        total_nb_tasks = await get_total_nb_of_tasks(
            project_id=project_id,
            filters=filters,
        )
        output["total_nb_tasks"] = total_nb_tasks
        logger.info(f"Total nb tasks: {total_nb_tasks}")
        if total_nb_tasks is not None:
            if limit is not None:
                nb_elements = min(total_nb_tasks, limit)
            else:
                nb_elements = total_nb_tasks

    elif query.scope == "users":
        total_nb_users = await get_total_nb_of_users(
            project_id=project_id,
            filters=filters,
        )
        output["total_nb_users"] = total_nb_users
        if limit is not None and total_nb_users is not None:
            output["nb_users_in_scope"] = min(total_nb_users, limit)
        else:
            output["nb_users_in_scope"] = total_nb_users

        nb_users_messages = await get_nb_users_messages(
            project_id=project_id,
            filters=filters,
            limit=cast(int | None, output["nb_users_in_scope"]),
        )
        output["nb_users_messages"] = nb_users_messages
        if nb_users_messages is not None:
            nb_elements = nb_users_messages

    if nb_elements is not None:
        clustering_cost = 2 * nb_elements
    else:
        clustering_cost = None

    logger.info(f"Clustering cost for project {project_id}: {clustering_cost}")

    return {
        "clustering_cost": clustering_cost,
        "nb_elements": nb_elements,
        **output,
    }


@router.post(
    "/explore/{project_id}/aggregated/events",
    description="Get aggregated metrics for the events of a project. Used for the Events dashboard.",
)
async def get_events_project_metrics(
    project_id: str,
    metrics: Optional[List[str]] = None,
    filters: Optional[ProjectDataFilters] = None,
    user: User = Depends(propelauth.require_user),
):
    """
    Get aggregated metrics for the events of a project. Used for the Events dashboard.
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)
    # Convert to UNIX timestamp in seconds
    if filters is None:
        filters = ProjectDataFilters()
    if isinstance(filters.created_at_start, datetime.datetime):
        filters.created_at_start = int(filters.created_at_start.timestamp())
    if isinstance(filters.created_at_end, datetime.datetime):
        filters.created_at_end = int(filters.created_at_end.timestamp())

    output = await get_events_aggregated_metrics(
        project_id=project_id,
        metrics=metrics,
        filters=filters,
    )
    return output


@router.post(
    "/explore/{project_id}/aggregated/users",
    description="Get aggregated metrics for the users of a project. Used for the Users dashboard.",
)
async def get_users_project_metrics(
    project_id: str,
    metrics: Optional[List[str]] = None,
    filters: Optional[ProjectDataFilters] = None,
    user: User = Depends(propelauth.require_user),
):
    """
    Get aggregated metrics for the users of a project. Used for the Users dashboard.
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)
    # Convert to UNIX timestamp in seconds
    if filters is None:
        filters = ProjectDataFilters()
    if isinstance(filters.created_at_start, datetime.datetime):
        filters.created_at_start = int(filters.created_at_start.timestamp())
    if isinstance(filters.created_at_end, datetime.datetime):
        filters.created_at_end = int(filters.created_at_end.timestamp())

    output = await get_users_aggregated_metrics(
        project_id=project_id,
        metrics=metrics,
        filters=filters,
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
    filters: Optional[ProjectDataFilters] = None,
    user: User = Depends(propelauth.require_user),
) -> Events:
    await verify_if_propelauth_user_can_access_project(user, project_id)

    events = await get_all_events(project_id=project_id, limit=limit, filters=filters)
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


@router.post(
    "/explore/{project_id}/clusterings",
    response_model=Clusterings,
    description="Get the all the clusterings of a project",
)
async def post_all_clusterings(
    project_id: str,
    user: User = Depends(propelauth.require_user),
) -> Clusterings:
    """
    Get all the clusterings of a project.

    Clusterings are groups of clusters.
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)
    clusterings = await fetch_all_clusterings(project_id=project_id)
    return Clusterings(clusterings=clusterings)


@router.post(
    "/explore/{project_id}/clusterings/{clustering_id}",
    response_model=Clustering,
    description="Get the all the clusterings of a project",
)
async def post_selected_clustering(
    project_id: str,
    clustering_id: str,
    user: User = Depends(propelauth.require_user),
) -> Clustering:
    """
    Update the status of the selected clustering.
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)
    clustering = await get_clustering_by_id(
        project_id=project_id, clustering_id=clustering_id
    )
    return clustering


@router.post(
    "/explore/{project_id}/clusters",
    response_model=Clusters,
    description="Get the different clusters of a project",
)
async def post_all_clusters(
    project_id: str,
    query: Optional[FetchClustersRequest] = None,
    user: User = Depends(propelauth.require_user),
) -> Clusters:
    """
    Get all the clusters of a project.

    Clusters are groups of tasks.
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)
    if query is None:
        query = FetchClustersRequest()
    clusters = await fetch_all_clusters(
        project_id=project_id,
        clustering_id=query.clustering_id,
        limit=query.limit,
    )
    return Clusters(clusters=clusters)


@router.post(
    "/explore/{project_id}/clusters/{cluster_id}",
    response_model=Cluster,
    description="Get the different clusters of a project",
)
async def post_single_cluster(
    project_id: str,
    cluster_id: str,
    user: User = Depends(propelauth.require_user),
) -> Cluster:
    """
    Get a cluster data
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)
    cluster = await fetch_single_cluster(project_id=project_id, cluster_id=cluster_id)
    if cluster is None:
        raise HTTPException(
            status_code=404,
            detail=f"Cluster {cluster_id} not found in project {project_id}",
        )
    return cluster


@router.post(
    "/explore/{project_id}/detect-clusters",
    response_model=Clustering,
    description="Run the clusters detection algorithm on a project",
)
async def post_detect_clusters(
    project_id: str,
    query: DetectClustersRequest,
    background_tasks: BackgroundTasks,
    user: User = Depends(propelauth.require_user),
) -> Clustering:
    """
    Run the clusters detection algorithm on a project.

    Returns a dummy clustering object, used for the frontend.
    """
    org_id = await verify_if_propelauth_user_can_access_project(user, project_id)

    logger.debug(f"clustering mode:{query.clustering_mode}")
    logger.debug(f"scope:{query.scope}")

    usage_quota = await get_quota_for_org(org_id)
    current_usage = usage_quota.current_usage
    max_usage = usage_quota.max_usage

    total_nb_messages: int | None = None
    if query.scope == "messages":
        total_nb_messages = await get_total_nb_of_tasks(
            project_id=project_id, filters=query.filters
        )
        if query.limit and total_nb_messages:
            total_nb_messages = min(total_nb_messages, query.limit)
    elif query.scope == "sessions":
        total_nb_messages = await get_nb_tasks_in_sessions(
            project_id=project_id, filters=query.filters, limit=query.limit
        )
    elif query.scope == "users":
        total_nb_messages = await get_nb_users_messages(
            project_id=project_id, filters=query.filters, limit=query.limit
        )
    else:
        raise HTTPException(
            status_code=400,
            detail="Scope should be messages, sessions or users.",
        )

    if total_nb_messages is None:
        raise HTTPException(
            status_code=404,
            detail="No tasks found in the project.",
        )

    credits_to_bill = total_nb_messages * 2

    logger.info(
        f"We will bill {credits_to_bill} credits for project clustering {project_id}"
    )

    # Ignore limits and metering in preview mode
    if config.ENVIRONMENT != "preview":
        if usage_quota.plan == "hobby" or usage_quota.plan is None:
            if max_usage is not None and current_usage + total_nb_messages >= max_usage:
                raise HTTPException(
                    status_code=403,
                    detail="Payment details required to run the cluster detection algorithm.",
                )

    if query.filters is None:
        query.filters = ProjectDataFilters()

    # Generate a unique id for the clustering and a valid name
    clustering_id = generate_uuid()
    clustering_name = generate_version_id()
    clustering_request = ClusteringRequest(
        org_id=org_id,
        project_id=project_id,
        # model=query.model, # Not implemented yet, always usel latest model
        limit=query.limit,
        filters=query.filters,
        instruction=query.instruction,
        nb_clusters=query.nb_clusters,
        # merge_clusters=query.merge_clusters, # Not implemented yet
        customer_id=usage_quota.customer_id,
        nb_credits_used=credits_to_bill,
        clustering_id=clustering_id,
        clustering_name=clustering_name,
        clustering_mode=query.clustering_mode,
        user_email=user.email,
        scope=query.scope,
        output_format=query.output_format,
    )
    logger.info(
        f"Clustering id {clustering_id} cluster name {clustering_name} for project {project_id} requested."
    )

    ai_hub_client = AIHubClient(org_id=org_id, project_id=project_id)
    background_tasks.add_task(
        ai_hub_client.run_clustering,
        clustering_request=clustering_request,
    )

    # Return a dummy clustering object, used for the frontend
    return Clustering(
        org_id=org_id,
        project_id=project_id,
        id=clustering_id,
        name=clustering_name,
        model=clustering_request.model,
        scope=query.scope,
        instruction=clustering_request.instruction,
        nb_clusters=None,
        clusters_ids=[],
        status="started",
    )


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


@router.post(
    "/explore/{project_id}/aggregated/events/{event_id}",
    description="Get aggregated metrics for an event. Used for the Events dashboard.",
)
async def get_event_detection_metrics(
    project_id: str,
    event_id: str,
    metrics: Optional[List[str]] = None,
    filters: Optional[ProjectDataFilters] = None,
    user: User = Depends(propelauth.require_user),
) -> dict:
    """
    Get aggregated metrics for an event. Used for the event dashboard.
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)
    logger.info(f"Event request: {event_id} {filters}")
    event = await get_event_definition_from_event_id(
        project_id=project_id, event_id=event_id
    )
    logger.info(f"Event: {event}")

    # Convert to UNIX timestamp in seconds
    if filters is None:
        filters = ProjectDataFilters()
    if isinstance(filters.created_at_start, datetime.datetime):
        filters.created_at_start = int(filters.created_at_start.timestamp())
    if isinstance(filters.created_at_end, datetime.datetime):
        filters.created_at_end = int(filters.created_at_end.timestamp())

    # Override the event_id filter
    filters.event_id = [event.id]

    output = await get_events_aggregated_metrics(
        project_id=project_id,
        metrics=metrics,
        filters=filters,
    )
    logger.info(f"Event output: {output}")
    return output


@router.post(
    "/explore/{project_id}/ab-tests/compare-versions",
    description="Get the number of times each item was observed in the two versions of an AB test.",
)
async def get_ab_tests_comparison(
    project_id: str,
    versions: ABTestVersions,
    user: User = Depends(propelauth.require_user),
) -> List[Dict[str, Union[str, float, int]]]:
    await verify_if_propelauth_user_can_access_project(user, project_id)
    logger.debug(f"AB tests comparison: {versions}")
    output = await get_ab_tests_versions(
        project_id=project_id,
        versionA=versions.versionA,
        versionB=versions.versionB,
        selected_events_ids=versions.selected_events_ids,
        filtersA=versions.filtersA,
        filtersB=versions.filtersB,
    )
    return output


@router.post(
    "/explore/{project_id}/data-cloud",
    response_model=dict,
    description="Get the data for the clustering cloud.",
)
async def get_data_cloud(
    project_id: str,
    version: ClusteringEmbeddingCloud,
    user: User = Depends(propelauth.require_user),
) -> dict:
    """
    This endpoint is used to get the data for the clustering cloud.

    This data is compatible with the plotly frontend library.
    """
    logger.debug(f"{version.model_dump()}")
    await verify_if_propelauth_user_can_access_project(user, project_id)
    logger.debug(f"Cloud data request: {version}")
    output = await compute_cloud_of_clusters(
        project_id=project_id,
        version=version,
    )
    return output
