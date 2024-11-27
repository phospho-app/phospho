from typing import List, Optional

from loguru import logger
from phospho import lab
from phospho.lab import Message
from phospho.models import ProjectDataFilters, Session

from ai_hub.db.sessions import load_sessions
from ai_hub.models.users import User
from ai_hub.services.summaries import generate_intent_summary_phospho_job


async def format_user_messages(
    datas: List[User],
    model_llm: str,
    provider: str,
    instruction: Optional[str] = "user intent",
) -> List[Message]:
    """
    For each user, generate a summary of each session and return a message with all the summaries.
    """
    project_id = datas[0].project_id

    user_messages: List[Message] = []
    for user in datas:
        messages: List[Message] = []
        user_interactions = ""
        # Get the user sessions thanks to the user.session_ids attribute
        logger.debug(f"User {user.id} has {len(user.sessions_ids)} sessions")
        sessions = await load_sessions(
            project_id=project_id,
            filters=ProjectDataFilters(
                sessions_ids=[
                    session_id
                    for session_id in user.sessions_ids
                    if isinstance(session_id, str)
                ],
            ),
        )
        if sessions is None:
            sessions = []
        sessions = [Session.model_validate(session) for session in sessions]
        logger.debug(f"Nb sessions: {len(sessions)}")
        # Compute a summary for each session of the user
        for i, session in enumerate(sessions):
            try:
                message = lab.Message.from_session(
                    session,
                    metadata={
                        "session_id": session.id,
                        # We don't keep any reference to the tasks of the sessions, to avoid confusion
                        "task_id": None,
                    },
                )
                messages.append(message)
            except ValueError:
                logger.warning(f"Session {session.id} is empty. Skipping")
                continue
            except Exception as e:
                logger.error(f"Error while generating messages: {e}")
                continue

        logger.debug(f"Nb messages: {len(messages)}")

        workload = lab.Workload(
            jobs=[
                lab.Job(
                    id="intent_summary",
                    job_function=generate_intent_summary_phospho_job,
                    config=lab.JobConfig(
                        model_llm=model_llm,
                        provider=provider,
                        instruction=instruction,
                        scope="sessions",
                    ),
                ),
            ]
        )
        await workload.async_run(messages, max_parallelism=100)

        if workload.results is None:
            user_messages.append(
                lab.Message(
                    role="user",
                    content="No data for this user",
                    metadata={"user_id": user.id},
                )
            )
            continue  # Skip

        # Concatenate the summaries of the sessions in the message.content
        for i, (message_id, job_results) in enumerate(workload.results.items()):
            user_interactions += f"<interaction {i}>\n"
            if job_results["intent_summary"].result_type == lab.ResultType.error:
                logger.warning(
                    f"Error while generating intent summary for message {message_id}. Skipping"
                )
            else:
                user_interactions += job_results["intent_summary"].value

            user_interactions += "\n</interaction {i}>\n"

        user_messages.append(
            lab.Message(
                role="user",
                content=user_interactions,
                metadata={"user_id": user.id},
            )
        )
    return user_messages
