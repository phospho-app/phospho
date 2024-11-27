import os
import time
from typing import Dict, List, Optional

from email_event import EmailEventlModel
from pydantic import BaseModel
from pymongo import MongoClient

# Set the MONGODB_URL and MONGODB_NAME environment variables
MONGODB_URL = os.getenv("MONGODB_URL")
if MONGODB_URL is None:
    raise Exception("MONGODB_URL is not set in the environment variables")
MONGODB_NAME = os.getenv("MONGODB_NAME")
if MONGODB_NAME is None:
    raise Exception("MONGODB_NAME is not set in the environment variables")

# Create a MongoClient to the running MongoDB instance
client: MongoClient = MongoClient(MONGODB_URL)

# Access or create a database called 'mydatabase'
db = client[MONGODB_NAME]


def check_email_never_sent_for_org(event_name: str, org_id: str) -> bool:
    """
    Checks if the event has already been sent to the organization.
    """
    # Check if there is a document in the 'events' collection with the event_name and org_id
    event = db["event_emails"].find_one({"event_name": event_name, "org_id": org_id})

    # If there is no document, the event wasn't already sent. We can send it.
    if event is None:
        return True
    else:
        return False


def save_email_event(
    event_name: str, org_id: str, email_subject: str, email_content: str
):
    """
    Saves the event in the database
    """
    event_email_data = EmailEventlModel(
        event_name=event_name,
        org_id=org_id,
        email_subject=email_subject,
        email_content=email_content,
    )

    # Insert a document in the 'events' collection with the event_name and org_id
    db["event_emails"].insert_one(event_email_data.model_dump())

    # Check if it has been inserted
    event = db["event_emails"].find_one({"event_name": event_name, "org_id": org_id})
    if event is None:
        raise Exception("The event has not been saved in the database")
    else:
        return True


### Functions to validate events ###
def validate_1_task_event(org_id: str) -> bool:
    """
    Checks if the organization has logged at least one task and less than 99 tasks
    """
    # Fetch the tasks of the organization
    task_count = db["tasks"].count_documents({"org_id": org_id})

    # If there is at least one task, the event is validated
    if task_count > 0 and task_count < 100:
        return True
    else:
        return False


def validate_100_tasks_event(org_id: str) -> bool:
    """
    Checks if the organization has logged at least 100 tasks and less than 1000 tasks
    """
    # Fetch the tasks of the organization
    task_count = db["tasks"].count_documents({"org_id": org_id})

    # If there are at least 100 tasks, the event is validated
    if task_count >= 100 and task_count < 1000:
        return True
    else:
        return False


def validate_1000_tasks_event(org_id: str) -> bool:
    """
    Checks if the organization has logged at least 1000 tasks and less than 1100 tasks
    """
    # Fetch the tasks of the organization
    task_count = db["tasks"].count_documents({"org_id": org_id})

    # If there are at least 1000 tasks, the event is validated
    if task_count >= 1000 and task_count < 1100:
        return True
    else:
        return False


def validate_no_task_for_1_week_event(org_id: str) -> bool:
    """
    Checks if the organization has not logged any task for 1 week
    """
    # Calculate the threshold timestamp for 7 days ago
    current_time = time.time()
    seven_days_ago = current_time - (7 * 24 * 60 * 60)  # 7 days in seconds

    # Construct the query to find at least one document matching the criteria
    query = {"org_id": org_id, "created_at": {"$gt": seven_days_ago}}

    # Fetch the tasks of the organization that have a timestamp of less than a week
    tasks = db["tasks"].find_one(query)

    # Check if there is a task or not
    if tasks is None:
        return True
    else:
        return False


def validate_no_session_for_1_week_event(org_id: str) -> bool:
    """
    Checks if the organization has not logged any session for 1 week
    """
    # Calculate the threshold timestamp for 7 days ago
    current_time = time.time()
    seven_days_ago = current_time - (7 * 24 * 60 * 60)  # 7 days in seconds

    # Construct the query to find at least one document matching the criteria
    query = {"org_id": org_id, "created_at": {"$gt": seven_days_ago}}

    # Fetch the sessions of the organization that have a timestamp of less than a week
    sessions = db["sessions"].find_one(query)

    # Check if there is a session or not
    if sessions is None:
        return True
    else:
        return False


class WeeklyReportKpisModel(BaseModel):
    most_active_project: Dict[str, int]
    nb_tasks: int
    nb_sessions: int
    nb_events: int
    top_events: List[Dict[str, int]]


def get_last_week_kpis(org_id: str) -> Optional[WeeklyReportKpisModel]:
    """
    Get activity KPIS for the last week and return them
    """
    # Calculate the threshold timestamp for 7 days ago
    current_time = time.time()
    seven_days_ago = current_time - (7 * 24 * 60 * 60)  # 7 days in seconds

    # Find out what project was the most active in the last week
    most_active_projects = list(
        db["tasks"].aggregate(
            [
                {"$match": {"org_id": org_id, "created_at": {"$gt": seven_days_ago}}},
                {
                    "$group": {
                        "_id": "$project_id",
                        "count": {"$sum": 1},
                    }
                },
                {"$sort": {"count": -1}},
                {"$limit": 1},
                {
                    "$lookup": {
                        "from": "projects",
                        "localField": "_id",
                        "foreignField": "id",
                        "as": "project",
                    }
                },
                {
                    "$unwind": "$project",
                },
                {
                    "$project": {
                        "_id": 1,
                        "project_name": "$project.project_name",
                        "nb_tasks": "$count",
                    }
                },
            ]
        )
    )
    assert most_active_projects is not None
    if len(most_active_projects) == 0:
        return None

    most_active_project = most_active_projects[0]

    # Compute the number of tasks and sessions for the organization
    # that have been created in the last week
    tasks = db["tasks"].count_documents(
        {"org_id": org_id, "created_at": {"$gt": seven_days_ago}}
    )
    sessions = db["sessions"].count_documents(
        {"org_id": org_id, "created_at": {"$gt": seven_days_ago}}
    )

    # Compute the top 3 most detected events for the organization
    # that have been created in the last week
    top_events = list(
        db["events"].aggregate(
            [
                {
                    "$match": {"org_id": org_id, "created_at": {"$gt": seven_days_ago}},
                    "removed": {"$ne": True},
                },
                {"$group": {"_id": "$event_name", "count": {"$sum": 1}}},
                {"$sort": {"count": -1}},
                {"$limit": 3},
                {
                    "$project": {
                        "_id": 0,
                        "event_name": "$_id",
                        "nb_occurrences": "$count",
                    }
                },
            ]
        )
    )

    nb_events = db["events"].count_documents(
        {
            "org_id": org_id,
            "created_at": {"$gt": seven_days_ago},
            "removed": {"$ne": True},
        }
    )

    return WeeklyReportKpisModel(
        most_active_project=most_active_project,
        nb_tasks=tasks,
        nb_sessions=sessions,
        top_events=top_events,
        nb_events=nb_events,
    )


def orga_nb_tasks_last_week(
    org_id: str,
) -> int:
    """
    This is used to determine if the organization was active last week,
    before sending weekly report with KPIs.
    """
    # Calculate the threshold timestamp for 7 days ago
    current_time = time.time()
    seven_days_ago = current_time - (7 * 24 * 60 * 60)  # 7 days in seconds

    # The org has been active if there are more than 3 tasks last week
    nb_tasks = db["tasks"].count_documents(
        {"org_id": org_id, "created_at": {"$gt": seven_days_ago}}
    )
    return nb_tasks
