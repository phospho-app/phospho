"""
This agent is called by the CICD after deploying to staging.
This is part of integration testing.
We check that the onboarding and logging flow works as expected.
"""

import os
import time
import phospho
import requests  # type: ignore
import openai


def test_onboarding(backend_url, org_id, access_token, api_key):
    # Create a new project
    project = requests.post(
        f"{backend_url}/api/organizations/{org_id}/projects",
        json={"project_name": "test"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert project.status_code == 200, project.reason
    project_id = project.json()["id"]

    # Check that the project exists
    projects = requests.get(
        f"{backend_url}/api/organizations/{org_id}/projects",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert projects.status_code == 200, projects.reason
    assert project_id in [p["id"] for p in projects.json()["projects"]]

    # Log to the project
    phospho.init(
        api_key=api_key,
        project_id=project_id,
        base_url=f"{backend_url}/v2",
        tick=0.1,
        auto_log=False,  # We automatically log tasks in the background, we disable it here because we don't want his behavior
    )
    # Task 1
    task_1 = phospho.log(
        input="Thank you!",
        output="You're welcome.",
        metadata={"text": "metadata", "number": 333},
    )
    time.sleep(1)

    class OpenAIAgent:
        def __init__(self):
            self.openai_client = openai.Client(api_key=os.environ["OPENAI_API_KEY"])

        @phospho.wrap(
            stream=True,
            stop=lambda x: x is None,
            input_to_str_function=lambda x: x["question"],
        )
        def ask(self, question: str, session_id: str):
            response = self.openai_client.chat.completions.create(
                messages=[
                    {"role": "system", "content": "Answer yes"},
                    {"role": "user", "content": question},
                ],
                max_tokens=3,
                model="gpt-4o-mini",
                stream=True,
            )
            for rep in response:
                yield rep.choices[0].delta.content

    # Task 2
    session_id = phospho.new_session()
    agent = OpenAIAgent()
    response = agent.ask(question="Are you an AI?", session_id=session_id)
    "".join(
        [r for r in response if r is not None]
    )  # Consume the generator, this is important

    phospho.consumer.send_batch()

    # Wait for the pipeline to complete
    time.sleep(10)

    # Check that the tasks was logged to phospho
    tasks = requests.get(
        f"{backend_url}/api/projects/{project_id}/tasks",
        headers={
            "Authorization": f"Bearer {access_token}",
        },
    )
    assert tasks.status_code == 200, tasks.reason
    tasks_content = tasks.json()["tasks"]
    assert len(tasks.json()["tasks"]) == 2, tasks_content

    for task in tasks_content:
        if task["id"] == task_1["task_id"]:
            assert task["input"] == "Thank you!", tasks_content
            assert task["output"] == "You're welcome.", tasks_content
            assert task["metadata"]["text"] == "metadata", tasks_content
            assert task["metadata"]["number"] == 333, tasks_content
        else:
            assert task["input"] == "Are you an AI?", tasks_content
            # ChatGPt outputs are not deterministic, so we only check that it contains "Yes"
            assert "yes" in task["output"].lower(), tasks_content

            # Check that there are some events in the log
            assert task["events"] is not None, tasks_content
            # assert task["flag"] is not None, tasks_content

    time.sleep(5)

    # Check that the session was created
    sessions = requests.get(
        f"{backend_url}/api/projects/{project_id}/sessions",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert sessions.status_code == 200, sessions.reason
    sessions_data = sessions.json()["sessions"]
    # We have 2 tasks, so we should have 2 sessions (tasks without session_id are created)
    assert len(sessions_data) == 2, sessions.json()
    # Order the sessions by increasing last_message_ts
    sessions_data = sorted(sessions_data, key=lambda x: x["created_at"])
    assert sessions_data[0]["id"].startswith("session_"), sessions_data
    assert sessions_data[1]["id"] == session_id, sessions_data
    # Call the dashboards
    # aggregated_metrics = requests.post(
    #     f"{backend_url}/api/explore/{project_id}/aggregated/",
    #     headers={"Authorization": f"Bearer {access_token}"},
    # )
    # assert aggregated_metrics.status_code == 200, aggregated_metrics.reason
    # aggregated_tasks = requests.post(
    #     f"{backend_url}/api/explore/{project_id}/aggregated/tasks",
    #     headers={"Authorization": f"Bearer {access_token}"},
    # )
    # assert aggregated_tasks.status_code == 200, aggregated_tasks.reason
    # aggregated_sessions = requests.post(
    #     f"{backend_url}/api/explore/{project_id}/aggregated/sessions",
    #     headers={"Authorization": f"Bearer {access_token}"},
    # )
    # assert aggregated_sessions.status_code == 200, aggregated_sessions.reason

    # Delete project
    delete_project = requests.delete(
        f"{backend_url}/api/projects/{project_id}/delete",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert delete_project.status_code == 200, delete_project.reason
