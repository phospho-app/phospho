import phospho_backend.core.config as config
from phospho_backend.api.v2.models import Project
from phospho_backend.main import app as router
from phospho_backend.utils import generate_uuid
from fastapi.testclient import TestClient
import pymongo

assert config.ENVIRONMENT != "production"


# We redefine cleanup here to be able to run tests locally
def cleanup(
    mongo_db: pymongo.MongoClient,
    collections_to_cleanup: dict[str, list[str]],
) -> None:
    """
    DELETE the documents in the collections specified in the collections_to_cleanup dict

    collections_to_cleanup is a dict of {collection_name: [list of ids]}
    those ids will be used to DELETE the documents in the collection
    """
    # Clean up database after the test
    if mongo_db.name != "production":
        for collection, values in collections_to_cleanup.items():
            mongo_db[collection].delete_many({"id": {"$in": values}})
    else:
        raise RuntimeError(
            "You are trying to clean the production database. Set MONGODB_NAME to something else than 'production'"
        )


# Platform tests
def test_create_and_delete_project(mongo_db, org_id, access_token):
    with TestClient(router) as client:
        # Create a project
        response = client.post(
            f"/api/organizations/{org_id}/projects",
            json={"project_name": "test"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200, response.text
        project = Project.model_validate(response.json())
        # CLEANUP["projects"].append(project.id)

        # Delete the project
        response = client.delete(
            f"/api/projects/{project.id}/delete",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200, response.text
    cleanup(mongo_db, {"projects": [project.id]})


def test_tasks_and_sessions(
    mongo_db,
    dummy_project,
    access_token,
    api_key,
):
    with TestClient(router) as client:
        # Get tasks
        response = client.get(
            f"/api/projects/{dummy_project.id}/tasks",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200, response.text
        tasks = response.json()["tasks"]
        assert len(tasks) == 0

        # Get sessions
        response = client.get(
            f"/api/projects/{dummy_project.id}/sessions",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200, response.text
        sessions = response.json()["sessions"]
        assert len(sessions) == 0

        # Insert a task in the db
        task = {
            "project_id": dummy_project.id,
            "task_id": generate_uuid(),
            "input": "test",
            "output": "test",
        }
        response = client.post(
            "/v2/tasks",
            json=task,
            headers={"Authorization": f"Bearer {api_key}"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["id"] == task["task_id"]
        assert response.json()["project_id"] == task["project_id"]

        # Get tasks
        response = client.get(
            f"/api/projects/{dummy_project.id}/tasks",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200, response.text
        tasks = response.json()["tasks"]
        assert len(tasks) == 1

        # Insert a session in the db
        session = {
            "project_id": dummy_project.id,
            "session_id": "test",
        }
        response = client.post(
            "/v2/sessions",
            json=session,
            headers={"Authorization": f"Bearer {api_key}"},
        )

        # Get sessions
        response = client.get(
            f"/api/projects/{dummy_project.id}/sessions",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200, response.text
        sessions = response.json()["sessions"]
        assert len(sessions) == 1

    cleanup(
        mongo_db,
        {"tasks": [task["task_id"]], "sessions": [session["session_id"]]},
    )


def test_create_and_update_task(
    dummy_project,
    mongo_db,
    access_token,
    api_key,
):
    with TestClient(router) as client:
        # Create a task
        task_original = {
            "project_id": dummy_project.id,
            "input": "test",
            "output": "test",
            "flag": "failure",
        }
        response = client.post(
            "/v2/tasks",
            json=task_original,
            headers={"Authorization": f"Bearer {api_key}"},
        )
        assert response.status_code == 200, response.text
        task = response.json()

        # API test

        # Update the task
        response = client.post(
            f"/api/tasks/{task['id']}",
            json={"metadata": {"some": "metadata"}},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["metadata"] == {"some": "metadata"}

        # Get the task
        response = client.get(
            f"/api/tasks/{task['id']}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["metadata"] == {"some": "metadata"}

        # Flag the task
        response = client.post(
            f"/api/tasks/{task['id']}/human-eval",
            json={"human_eval": "success"},
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["flag"] == "success"

        # Get the task
        response = client.get(
            f"/api/tasks/{task['id']}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["flag"] == "success"

        # v2 test

        # Update the task
        response = client.post(
            f"/v2/tasks/{task['id']}",
            json={"metadata": {"new": "metadata"}},
            headers={"Authorization": f"Bearer {api_key}"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["metadata"] == {"new": "metadata"}

        # Get the task
        response = client.get(
            f"/api/tasks/{task['id']}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["metadata"] == {"new": "metadata"}

        # Flag the task
        response = client.post(
            f"/v2/tasks/{task['id']}/human-eval",
            json={"human_eval": "failure"},
            headers={"Authorization": f"Bearer {api_key}"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["flag"] == "failure"

        # Get the task
        response = client.get(
            f"/api/tasks/{task['id']}",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert response.status_code == 200, response.text
        assert response.json()["flag"] == "failure"

    cleanup(mongo_db, {"tasks": [task["id"]]})


# API v2 tests


def test_log(
    mongo_db,
    api_key,
    minimal_log_content,
    dummy_project,
):
    with TestClient(router) as client:
        # Log an event to project
        response = client.post(
            f"/v2/log/{dummy_project.id}",
            json={"batched_log_events": minimal_log_content},
            headers={"Authorization": f"Bearer {api_key}"},
        )

        assert response.status_code == 200
        assert len(response.json()["logged_events"]) == len(minimal_log_content)
        for i, logged_event in enumerate(response.json()["logged_events"]):
            if i == 5 or i == 1:
                assert "error_in_log" in logged_event
            else:
                assert "project_id" in logged_event
                assert logged_event["project_id"] == dummy_project.id

                assert "task_id" in logged_event
                # CLEANUP["tasks"].append(logged_event["task_id"])
                if i == 2 or i == 3:
                    assert logged_event["session_id"] == "test"

    cleanup(
        mongo_db,
        {
            "tasks": [
                log["task_id"]
                for log in response.json()["logged_events"]
                if "task_id" in log
            ]
        },
    )
