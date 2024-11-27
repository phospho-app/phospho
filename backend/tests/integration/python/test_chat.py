"""
This agent is called by the CICD after deploying to staging.
"""

import openai
import requests  # type: ignore


def test_chat(backend_url, org_id, access_token, api_key):
    # Create a new project
    project = requests.post(
        f"{backend_url}/api/organizations/{org_id}/projects",
        json={"project_name": "test"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert project.status_code == 200, project.reason
    project_id = project.json()["id"]

    # Call the chat API
    openai_client = openai.OpenAI(
        api_key=api_key, base_url=f"{backend_url}/v2/{project_id}/"
    )
    # Sync call
    response = openai_client.chat.completions.create(
        messages=[{"role": "system", "content": "Answer yes"}],
        model="openai:gpt-4o-mini",
    )
    assert response is not None

    # Streaming call
    response = openai_client.chat.completions.create(
        messages=[{"role": "system", "content": "Answer yes"}],
        model="openai:gpt-4o-mini",
        stream=True,
    )
    for message in response:
        assert message is not None

    # Sync call
    response = openai_client.chat.completions.create(
        messages=[{"role": "system", "content": "Answer yes"}],
        model="mistral:mistral-small-latest",
    )
    assert response is not None

    # Streaming call
    response = openai_client.chat.completions.create(
        messages=[{"role": "system", "content": "Answer yes"}],
        model="mistral:mistral-small-latest",
        stream=True,
    )
    for message in response:
        assert message is not None

    # Delete project
    delete_project = requests.delete(
        f"{backend_url}/api/projects/{project_id}/delete",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert delete_project.status_code == 200, delete_project.reason
