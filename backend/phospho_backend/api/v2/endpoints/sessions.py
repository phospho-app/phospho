from fastapi import APIRouter, Depends, HTTPException

from phospho_backend.api.v2.models import (
    Session,
    SessionCreationRequest,
    SessionUpdateRequest,
    Tasks,
)

from phospho_backend.security import (
    authenticate_org_key,
    verify_propelauth_org_owns_project_id,
)
from phospho_backend.services.mongo.sessions import (
    get_session_by_id,
    create_session,
    format_session_transcript,
    fetch_session_tasks,
    edit_session_metadata,
)

router = APIRouter(tags=["Sessions"])


@router.get(
    "/sessions/{session_id}",
    response_model=Session,
    description="Get a specific session",
)
async def get_session(
    session_id: str,
    org: dict = Depends(authenticate_org_key),
) -> Session:
    session_model = await get_session_by_id(session_id)
    await verify_propelauth_org_owns_project_id(org, session_model.project_id)
    return session_model


@router.post(
    "/sessions",
    response_model=Session,
    description="Create a new session",
)
async def post_create_session(
    sessionCreationRequest: SessionCreationRequest,
    org: dict = Depends(authenticate_org_key),
) -> Session:
    await verify_propelauth_org_owns_project_id(org, sessionCreationRequest.project_id)
    try:
        created_session = await create_session(
            project_id=sessionCreationRequest.project_id,
            data=sessionCreationRequest.data,
            org_id=org["org"].get("org_id"),
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Session creation failed: {e}")

    return created_session


@router.get(
    "/sessions/{session_id}/transcript",
    description="Get the transcript of a session",
)
async def get_session_transcript(
    session_id: str, org: dict = Depends(authenticate_org_key)
) -> dict:
    session = await get_session_by_id(session_id)
    await verify_propelauth_org_owns_project_id(org, session.project_id)
    transcript = format_session_transcript(session)
    return {"transcript": transcript}


@router.get(
    "/sessions/{session_id}/tasks",
    response_model=Tasks,
    description="Get all the tasks of a session",
)
async def get_session_tasks(
    session_id: str, limit: int = 1000, org: dict = Depends(authenticate_org_key)
) -> Tasks:
    # TODO : add pagination, filtering, sorting

    session = await get_session_by_id(session_id)
    await verify_propelauth_org_owns_project_id(org, session.project_id)
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
    org: dict = Depends(authenticate_org_key),
) -> Session:
    session_data = await get_session_by_id(session_id)
    await verify_propelauth_org_owns_project_id(org, session_data.project_id)
    session_data = await edit_session_metadata(
        session_data, **sessions_update_metadata_request.model_dump()
    )
    return session_data
