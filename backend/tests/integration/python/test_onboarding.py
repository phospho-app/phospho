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
        user_id="Nico le plus beau",
        metadata={"text": "metadata", "number": 333},
    )

    pivot_query = {
        "project_id": project_id,
        "metric": "nb_messages",
        "breakdown_by": "day",
    }
    # Call the export analytics API
    response = requests.post(
        f"{backend_url}/v3/export/analytics",
        json=pivot_query,
        headers={"Authorization": f"Bearer {api_key}"},
    )

    assert response.status_code == 200, response.reason
    assert response.json()["pivot_table"] is not None

    query = {
        "filters": {
            "created_at_start": "2024-01-01T00:00:00Z",
        },
        "pagination": {"page": 1, "per_page": 10},
        "sorting": [
            {"id": "user_id", "desc": True},
        ],
    }

    # Call the export users API
    response = requests.post(
        f"{backend_url}/v3/export/projects/{project_id}/users",
        json=query,
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert response.status_code == 200, response.reason
    assert response.json() is not None

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

    # Test the run v3 endpoints
    # messagesRequest = {
    #     "project_id": project_id,
    #     "messages": [
    #         {"role": "user", "content": "Hello"},
    #         {"role": "system", "content": "Hi"},
    #     ],
    # }

    # run_main_pipeline_on_messages = requests.post(
    #     f"{backend_url}/v3/run/main/messages",
    #     json=messagesRequest,
    #     headers={"Authorization": f"Bearer {api_key}"},
    # )

    # assert (
    #     run_main_pipeline_on_messages.status_code == 200
    # ), run_main_pipeline_on_messages.reason

    # # # Check that the sentiment dict is not empty
    # assert run_main_pipeline_on_messages.json()["sentiment"] is not None
    # assert len(run_main_pipeline_on_messages.json()["sentiment"]) > 0

    # # # Check that the language is not empty
    # assert run_main_pipeline_on_messages.json()["language"] is not None
    # assert len(run_main_pipeline_on_messages.json()["language"]) > 0

    # # # Check that the event dict is empty
    # assert run_main_pipeline_on_messages.json()["events"] is not None
    # assert len(run_main_pipeline_on_messages.json()["events"]) == 0

    # backtestRequest = {
    #     "project_id": project_id,
    #     "system_prompt_template": "Hello",
    #     "provider_and_model": "openai:gpt-4o-mini",
    # }

    # run_backtests = requests.post(
    #     f"{backend_url}/v3/run/backtest",
    #     json=backtestRequest,
    #     headers={"Authorization": f"Bearer {api_key}"},
    # )

    # assert run_backtests.status_code == 200, run_backtests.reason

    batched_log_events = [
        {
            "messages": [
                {
                    "role": "assistant",
                    "content": "Hello! I'm here to help you with anything you need today.",
                },
                {
                    "role": "user",
                    "content": "Thanks! Can you give me some tips on productivity?",
                },
                {
                    "role": "assistant",
                    "content": "Certainly! Try setting clear goals, using a timer for focused work sessions, and keeping a task list.",
                },
                {"role": "system", "content": "You are a life coach."},
                {
                    "role": "user",
                    "content": "Great advice! How about staying motivated?",
                },
                {
                    "role": "assistant",
                    "content": "Celebrate small wins along the way to keep the momentum going!",
                },
            ]
        },
        {
            "messages": [
                {
                    "role": "user",
                    "content": "Can you help me plan an essay on renewable energy?",
                },
                {
                    "role": "assistant",
                    "content": "Of course! A strong outline could include the benefits, challenges, and the future of renewable sources.",
                },
                {"role": "system", "content": "You are an environmental expert."},
                {
                    "role": "user",
                    "content": "Good idea. What specific examples should I include?",
                },
                {
                    "role": "assistant",
                    "content": "Consider mentioning solar and wind energy and how they’re impacting various regions worldwide.",
                },
            ]
        },
        {
            "messages": [
                {
                    "role": "assistant",
                    "content": "Hey there! Got any questions I can help with today?",
                },
                {"role": "user", "content": "What's the capital of Italy?"},
                {"role": "assistant", "content": "The capital of Italy is Rome!"},
                {"role": "user", "content": "And what about Spain?"},
                {"role": "assistant", "content": "Spain’s capital is Madrid."},
                {"role": "system", "content": "You are a geography expert."},
            ]
        },
        {
            "messages": [
                {
                    "role": "user",
                    "content": "I’m looking for book recommendations. Can you help?",
                },
                {
                    "role": "assistant",
                    "content": "Of course! Which genre do you have in mind?",
                },
                {"role": "user", "content": "I love mysteries."},
                {
                    "role": "assistant",
                    "content": "In that case, try *The Girl with the Dragon Tattoo* by Stieg Larsson. It’s captivating!",
                },
            ]
        },
        {
            "messages": [
                {"role": "system", "content": "You are a computer support assistant."},
                {
                    "role": "assistant",
                    "content": "Hello! How can I assist with your computer issues today?",
                },
                {"role": "user", "content": "My laptop keeps freezing."},
                {
                    "role": "assistant",
                    "content": "I see. Have you tried a full shutdown to reset everything?",
                },
                {"role": "user", "content": "Yes, but it didn’t help."},
                {
                    "role": "assistant",
                    "content": "Then let’s try checking for updates or removing unnecessary startup programs.",
                },
            ]
        },
        {
            "messages": [
                {
                    "role": "assistant",
                    "content": "Do you have any questions about technology?",
                },
                {
                    "role": "user",
                    "content": "Yes, actually! How does machine learning work?",
                },
                {
                    "role": "system",
                    "content": "You are an AI and machine learning specialist.",
                },
                {
                    "role": "assistant",
                    "content": "In simple terms, machine learning involves training algorithms on large datasets to identify patterns.",
                },
                {
                    "role": "user",
                    "content": "That’s interesting! Can you give a practical example?",
                },
                {
                    "role": "assistant",
                    "content": "Sure! For instance, facial recognition on phones is a type of machine learning application.",
                },
            ]
        },
        {
            "messages": [
                {
                    "role": "user",
                    "content": "I'm going to Japan soon! Any travel tips?",
                },
                {
                    "role": "assistant",
                    "content": "Fantastic! Make sure to explore both modern and traditional spots like Tokyo and Kyoto.",
                },
                {"role": "user", "content": "Any advice on budgeting for the trip?"},
                {"role": "system", "content": "You are a travel budgeting expert."},
                {
                    "role": "assistant",
                    "content": "Yes! Consider using Japan Rail Pass for trains, and try convenience stores for affordable, delicious meals!",
                },
            ]
        },
    ]
    log_requests = {"project_id": project_id, "batched_log_events": batched_log_events}
    response = requests.post(
        f"{backend_url}/v3/log",
        json=log_requests,
        headers={"Authorization": f"Bearer {api_key}"},
    )
    assert response.status_code == 200, response.reason

    delete_project = requests.delete(
        f"{backend_url}/api/projects/{project_id}/delete",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert delete_project.status_code == 200, delete_project.reason
