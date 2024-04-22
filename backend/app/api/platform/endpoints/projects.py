import datetime
from typing import Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends
from loguru import logger
from propelauth_fastapi import User

from app.api.platform.models import (
    Events,
    Project,
    ProjectUpdateRequest,
    SearchQuery,
    SearchResponse,
    Sessions,
    Tasks,
    Tests,
    AddEventsQuery,
    OnboardingSurvey,
    Users,
    OnboardingSurveyResponse,
    ProjectDataFilters,
    QuerySessionsTasksRequest,
)
from app.security.authentification import (
    propelauth,
    verify_if_propelauth_user_can_access_project,
)
from app.services.mongo.projects import (
    delete_project_from_id,
    delete_project_related_resources,
    email_project_tasks,
    get_all_events,
    get_all_sessions,
    get_all_tasks,
    get_all_tests,
    get_project_by_id,
    get_all_users_metadata,
    update_project,
    suggest_events_for_use_case,
    add_project_events,
    store_onboarding_survey,
)

from app.services.mongo.search import (
    search_tasks_in_project,
    search_sessions_in_project,
)

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
        sessions_filter=query.filters,
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


@router.post(
    "/projects/{project_id}/search/tasks",
    response_model=SearchResponse,
    description="Perform a semantic search in the project's sessions",
)
async def post_search_tasks(
    project_id: str,
    search_query: SearchQuery,
    user: User = Depends(propelauth.require_user),
):
    """
    Get the resulting session_ids of a semantic search in the project's sessions.
    The search is based on embedding similarity of the text conversation to the query.
    """

    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)
    # Perform the semantic search
    relevant_tasks = await search_tasks_in_project(
        project_id=project_id,
        search_query=search_query.query,
    )
    return SearchResponse(task_ids=[task.id for task in relevant_tasks])


@router.post(
    "/projects/{project_id}/search/sessions",
    response_model=SearchResponse,
    description="Perform a semantic search in the project's sessions",
)
async def post_search_sessions(
    project_id: str,
    search_query: SearchQuery,
    user: User = Depends(propelauth.require_user),
):
    """
    Get the resulting session_ids of a semantic search in the project's sessions.
    The search is based on embedding similarity of the text conversation to the query.
    """

    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)
    # Perform the semantic search
    relevant_tasks, relevant_sessions = await search_sessions_in_project(
        project_id=project_id,
        search_query=search_query.query,
    )
    return SearchResponse(
        task_ids=[task.id for task in relevant_tasks],
        session_ids=[session.id for session in relevant_sessions],
    )


@router.post(
    "/projects/{project_id}/tasks",
    response_model=Tasks,
    description="Get all the tasks of a project",
)
async def post_tasks(
    project_id: str,
    query: Optional[QuerySessionsTasksRequest] = None,
    user: User = Depends(propelauth.require_user),
):
    """
    Get all the tasks of a project.

    Args:
        project_id: The id of the project
        limit: The maximum number of tasks to return
    """
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)
    metadata_filter: Optional[Dict[str, object]] = None
    if query is None:
        query = QuerySessionsTasksRequest()
    if query.filters.user_id is not None:
        metadata_filter = {
            "user_id": query.filters.user_id,
        }

    tasks = await get_all_tasks(
        project_id=project_id,
        limit=None,
        validate_metadata=True,
        flag_filter=query.filters.flag,
        event_name_filter=query.filters.event_name,
        pagination=query.pagination,
        metadata_filter=metadata_filter,
        sorting=query.sorting,
        created_at_start=query.filters.created_at_start,
        created_at_end=query.filters.created_at_end,
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
    environment: Optional[str] = None,
    limit: int = 1000,
    user: User = Depends(propelauth.require_user),
) -> dict:
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)
    # Trigger the email sending in the background
    background_tasks.add_task(
        email_project_tasks, project_id=project_id, uid=user.user_id
    )
    logger.info(f"Emailing tasks of project {project_id} to {user.email}")
    return {"status": "ok"}


@router.get(
    "/projects/{project_id}/tests",
    response_model=Tests,
    description="Get all the tests of a project",
)
async def get_tests(
    project_id: str,
    limit: int = 1000,
    user: User = Depends(propelauth.require_user),
) -> Tests:
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)
    tests = await get_all_tests(project_id=project_id, limit=limit)
    return Tests(tests=tests)


@router.post(
    "/projects/{project_id}/suggest-events",
    description="Suggest events for a project (Onboarding)",
    response_model=OnboardingSurveyResponse,
)
async def suggest_events(
    project_id: str,
    survey: OnboardingSurvey,
    user: User = Depends(propelauth.require_user),
) -> OnboardingSurveyResponse:
    """
    Suggest events for a project based on the answers to an onboarding survey.

    This is part of the onboarding flow.
    """
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)
    await store_onboarding_survey(project_id, user, survey.model_dump())
    event_suggestions, phospho_task_id = await suggest_events_for_use_case(
        project_id=project_id, **survey.model_dump(), user_id=user.email
    )
    response = OnboardingSurveyResponse(
        suggested_events=event_suggestions, phospho_task_id=phospho_task_id
    )
    return response


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


@router.get(
    "/projects/{project_id}/users",
    response_model=Users,
    description="Get metadata about the end-users of a project",
)
async def get_users(
    project_id: str,
    user: User = Depends(propelauth.require_user),
) -> Users:
    """
    Get metadata about the end-users of a project
    """
    await verify_if_propelauth_user_can_access_project(user, project_id)
    users = await get_all_users_metadata(project_id)
    return Users(users=users)


@router.get(
    "/projects/{project_id}/unique-events",
    response_model=Events,
)
async def get_project_unique_events(
    project_id: str,
    events_filter: Optional[ProjectDataFilters] = None,
    user: User = Depends(propelauth.require_user),
) -> Events:
    """
    Get the unique observed events in a project
    """
    project = await get_project_by_id(project_id)
    propelauth.require_org_member(user, project.org_id)
    events = await get_all_events(
        project_id=project_id,
        events_filter=events_filter,
        include_removed=True,
        unique=True,
    )
    return Events(events=events)
