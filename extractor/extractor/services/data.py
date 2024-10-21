"""
Data pipeline related code
"""

from typing import List

from extractor.services.tasks import get_task_by_id
from extractor.db.mongo import get_mongo_db
from phospho.models import Task


async def fetch_previous_tasks(task_id: str) -> List[Task]:
    """
    Fetch all the previous tasks until the task, if the task is linked to a session.
    TODO : Query limits
    """
    # Get the document with a specific ID
    mongo_db = await get_mongo_db()
    task = await get_task_by_id(task_id)

    if task.session_id is None:
        return [task]

    # Get the tasks of the session before the task
    previous_tasks = (
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
    if previous_tasks is None:
        return [task]
    previous_tasks_models = [Task.model_validate(data) for data in previous_tasks]
    previous_tasks_models.append(task)
    return previous_tasks_models


def generate_task_transcript(
    list_of_task: List[Task],
    user_identifier="User:",
    assistant_identifier="Assistant:",
) -> str:
    """
    session_data : the session data
    user_identifier : the identifier of the messages of the end user (for the LLM)
    assistant_identifier : the identifier of the messages of the assistant (for the LLM)

    Returns a transcript of a task
    """
    transcript = ""
    for task in list_of_task:
        # Add the task name and description to the transcript
        transcript += f"{user_identifier} {task.input}\n"
        if task.output is not None:
            transcript += f"{assistant_identifier} {task.output}\n"

    return transcript


async def log_billing(
    credits_billed: int,
    org_id: str,
    project_id: str,
    action: str,
) -> None:
    """
    This function logs every billing action in the "billing" collection
    """
    mongo_db = await get_mongo_db()
    await mongo_db["billing"].insert_one(
        {
            "credits_billed": credits_billed,
            "org_id": org_id,
            "project_id": project_id,
            "action": action,
        }
    )
    return None
