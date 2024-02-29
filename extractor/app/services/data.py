"""
Data pipeline related code
"""
from typing import List
from loguru import logger

from app.services.tasks import get_task_by_id
from app.db.mongo import get_mongo_db
from app.db.models import Task


async def fetch_previous_tasks(task_id: str) -> List[Task]:
    """
    Fetch all the previous tasks until the task,
    if the task is linked to a session.

    TODO : query limits
    """
    # Get the document with a specific ID
    mongo_db = await get_mongo_db()
    task = await get_task_by_id(task_id)

    if task.session_id is None:
        return [task]

    # Get the tasks of the session before the task
    previous_taks = (
        await mongo_db["tasks"]
        .find(
            {
                "project_id": task.project_id,
                "session_id": task.session_id,
                "created_at": {"$lt": task.created_at},
            }
        )
        .sort("created_at", -1)
        .to_list(length=None)
    )
    if previous_taks is None:
        return [task]
    previous_taks_models = [Task.model_validate(data) for data in previous_taks]
    previous_taks_models.append(task)
    return previous_taks_models


def generate_task_transcript(
    list_of_task: List[Task],
    user_identifier="User:",
    assistant_identifier="Assistant:",
) -> str:
    """
    session_data : the session data
    user_identifier : the identifier of the messages of the end user (for the LLM)
    assistant_identifier : the identifier of the messages of the assistant (for the LLM)

    Returns a transcript of the session
    """
    transcript = ""
    for task in list_of_task:
        # Add the task name and description to the transcript
        transcript += f"{user_identifier} {task.input}\n"
        transcript += f"{assistant_identifier} {task.output or ' '}\n"

        # There is now the output in the task data

        # Add the output of the last step to the transcript
        # if len(step[1]) > 0:
        # If the last step is the finale step, we add the output to the transcript
        # if step[1][-1].get('is_last', False):
        # transcript += f"{assistant_identifier} {step[1][-1].get('output', ' ')}\n"

    return transcript
