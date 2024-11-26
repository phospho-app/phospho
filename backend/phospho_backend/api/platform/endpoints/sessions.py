from fastapi import APIRouter, Depends, HTTPException
from propelauth_fastapi import User

from phospho_backend.api.platform.models import (
    Session,
    SessionUpdateRequest,
    Tasks,
    SessionHumanEvalRequest,
)
from phospho_backend.security import verify_if_propelauth_user_can_access_project
from phospho_backend.security.authentification import propelauth
from phospho_backend.services.mongo.sessions import (
    edit_session_metadata,
    fetch_session_tasks,
    format_session_transcript,
    get_session_by_id,
    event_suggestion,
    human_eval_session,
)
from phospho_backend.api.platform.models import AddEventRequest, RemoveEventRequest
from phospho_backend.services.mongo.sessions import (
    add_event_to_session,
    remove_event_from_session,
)

router = APIRouter(tags=["Sessions"])


@router.get(
    "/sessions/{session_id}",
    response_model=Session,
    description="Get a specific session",
)
async def get_session(
    session_id: str, user: User = Depends(propelauth.require_user)
) -> Session:
    session = await get_session_by_id(session_id)
    await verify_if_propelauth_user_can_access_project(user, session.project_id)
    return session


@router.get(
    "/sessions/{session_id}/transcript",
    description="Get the transcript of a session",
)
async def get_session_transcript(
    session_id: str, user: User = Depends(propelauth.require_user)
) -> dict:
    session = await get_session_by_id(session_id)
    await verify_if_propelauth_user_can_access_project(user, session.project_id)
    transcript = format_session_transcript(session)
    return {"transcript": transcript}


@router.get(
    "/sessions/{session_id}/tasks",
    response_model=Tasks,
    description="Get all the tasks of a session",
)
async def get_session_tasks(
    session_id: str, limit: int = 1000, user: User = Depends(propelauth.require_user)
) -> Tasks:
    # TODO : add pagination, filtering, sorting

    session = await get_session_by_id(session_id)
    await verify_if_propelauth_user_can_access_project(user, session.project_id)
    tasks = await fetch_session_tasks(
        project_id=session.project_id, session_id=session_id, limit=limit
    )
    return Tasks(tasks=tasks)


@router.post(
    "/sessions/{session_id}",
    response_model=Session,
    description="Edit session metadata. Fields that are passed as None will not be updated.",
)
async def update_session_metadata(
    session_id: str,
    sessions_update_metadata_request: SessionUpdateRequest,
    user: User = Depends(propelauth.require_user),
) -> Session:
    session_data = await get_session_by_id(session_id)
    await verify_if_propelauth_user_can_access_project(user, session_data.project_id)
    session_data = await edit_session_metadata(
        session_data, **sessions_update_metadata_request.model_dump()
    )
    return session_data


@router.get(
    "/sessions/{session_id}/suggestion",
    description="Get an event suggestion based on a session",
)
async def get_session_suggestion(
    session_id: str, user: User = Depends(propelauth.require_user)
) -> list[str]:
    session = await get_session_by_id(session_id)
    await verify_if_propelauth_user_can_access_project(user, session.project_id)
    event_description = await event_suggestion(session_id)
    return event_description


@router.post(
    "/sessions/{session_id}/add-event",
    response_model=Session,
    description="Add an event to a session",
)
async def post_add_event_to_sessions(
    session_id: str,
    add_event: AddEventRequest,
    user: User = Depends(propelauth.require_user),
) -> Session:
    """
    Add an event to a session
    """
    session = await get_session_by_id(session_id)
    await verify_if_propelauth_user_can_access_project(user, session.project_id)

    updated_session = await add_event_to_session(
        session=session,
        event=add_event.event,
        score_range_value=add_event.score_range_value,
        score_category_label=add_event.score_category_label,
    )
    return updated_session


@router.post(
    "/sessions/{session_id}/remove-event",
    response_model=Session,
    description="Remove an event from a Session",
)
async def post_remove_event_from_session(
    session_id: str,
    remove_event: RemoveEventRequest,
    user: User = Depends(propelauth.require_user),
) -> Session:
    """
    Remove an event from a Session
    """
    session = await get_session_by_id(session_id)
    await verify_if_propelauth_user_can_access_project(user, session.project_id)

    updated_session = await remove_event_from_session(
        session=session,
        event_name=remove_event.event_name,
    )
    return updated_session


@router.post(
    "/sessions/{session_id}/human-eval",
    response_model=Session,
    description="Update the human eval of a session and the flag",
)
async def post_human_eval_session(
    session_id: str,
    sessionHumanEvalRequest: SessionHumanEvalRequest,
    user: User = Depends(propelauth.require_user),
) -> Session:
    """
    Update the human eval of a session and the session_flag with "success" or "failure"
    Also signs the origin of the flag with owner
    """
    if sessionHumanEvalRequest.human_eval not in ["success", "failure"]:
        raise HTTPException(
            status_code=400,
            detail="The human eval must be either 'success' or 'failure'",
        )
    session = await get_session_by_id(session_id)
    await verify_if_propelauth_user_can_access_project(user, session.project_id)
    updated_task = await human_eval_session(
        session_model=session,
        human_eval=sessionHumanEvalRequest.human_eval,
    )
    return updated_task
