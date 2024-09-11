from typing import List, Dict
from phospho.models import Task, Session, SessionStats
from app.utils import generate_uuid, get_most_common
from loguru import logger


def aggregate_tasks_into_sessions(tasks: List[Task], project_id: str) -> List[Session]:
    sessions: Dict[str, Session] = {}
    for task in tasks:
        if task.session_id is None:
            task.session_id = generate_uuid()
        if task.session_id not in sessions.keys():
            sessions[task.session_id] = Session(
                id=task.session_id,
                org_id=task.org_id,
                project_id=project_id,
                created_at=task.created_at,
                session_length=1,
                tasks=[task],
                preview=task.preview(),
            )
        else:
            if task.created_at < sessions[task.session_id].created_at:
                sessions[task.session_id].created_at = task.created_at
                sessions[task.session_id].preview = task.preview()
            sessions[task.session_id].session_length += 1
            session_tasks = sessions[task.session_id].tasks
            if session_tasks is not None:
                session_tasks.append(task)
            else:
                sessions[task.session_id].tasks = [task]

    validated_sessions: List[Session] = []
    # Process each session
    for sessions_id, session in sessions.items():
        if session.tasks is None:
            continue
        try:
            session.metadata = {
                "total_tokens": sum(
                    [
                        task.metadata["total_tokens"]
                        for task in session.tasks
                        if task.metadata is not None
                        and "total_tokens" in task.metadata
                        and task.metadata["total_tokens"] is not None
                    ]
                ),
                "prompt_tokens": sum(
                    [
                        task.metadata["prompt_tokens"]
                        for task in session.tasks
                        if task.metadata is not None
                        and "prompt_tokens" in task.metadata
                        and task.metadata["prompt_tokens"] is not None
                    ]
                ),
                "completion_tokens": sum(
                    [
                        task.metadata["completion_tokens"]
                        for task in session.tasks
                        if task.metadata is not None
                        and "completion_tokens" in task.metadata
                        and task.metadata["completion_tokens"] is not None
                    ]
                ),
            }
            session.stats = SessionStats(
                avg_magnitude_score=sum(
                    [
                        task.metadata["magnitude_score"]
                        for task in session.tasks
                        if task.metadata is not None
                        and "magnitude_score" in task.metadata
                        and task.metadata["magnitude_score"] is not None
                    ]
                )
                / session.session_length,
                avg_sentiment_score=sum(
                    [
                        task.metadata["sentiment_score"]
                        for task in session.tasks
                        if task.metadata is not None
                        and "sentiment_score" in task.metadata
                        and task.metadata["sentiment_score"] is not None
                    ]
                )
                / session.session_length,
                most_common_flag=get_most_common([task.flag for task in session.tasks]),
                most_common_language=get_most_common(
                    [task.language for task in session.tasks]
                ),
                most_common_sentiment_label=get_most_common(
                    [
                        task.metadata["sentiment_label"]
                        for task in session.tasks
                        if task.metadata is not None
                        and "sentiment_label" in task.metadata
                        and task.metadata["sentiment_label"] is not None
                    ]
                ),
                human_eval=get_most_common(
                    [
                        task.metadata["human_eval"]
                        for task in session.tasks
                        if task.metadata is not None
                        and "human_eval" in task.metadata
                        and task.metadata["human_eval"] is not None
                    ]
                ),
            )
            session.tasks = []
            logger.debug(f"Created session: {session.id}")
            validated_sessions.append(session)
        except Exception as e:
            logger.warning(f"Error creating session: {e}")
            continue

    logger.debug(f"Aggregated {len(validated_sessions)} sessions")

    return validated_sessions
