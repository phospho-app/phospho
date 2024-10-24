"""
This agent is called by the CICD after deploying to staging.

This agent tests the API endpoints of the export file in the backend.
"""

import phospho
import openai
import requests  # type: ignore


def test_export(backend_url, org_id, access_token, api_key):
    # Create a new project
    project = requests.post(
        f"{backend_url}/api/organizations/{org_id}/projects",
        json={"project_name": "test"},
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert project.status_code == 200, project.reason
    project_id = project.json()["id"]

    # init phospho

    phospho.init(project_id=project_id, api_key=api_key)

    openai_client = openai.OpenAI(
        api_key=api_key, base_url=f"{backend_url}/v2/{project_id}/"
    )

    # Call the chat API
    response = openai_client.chat.completions.create(
        messages=[{"role": "system", "content": "Hello !"}],
        model="openai:gpt-4o-mini",
    )
    assert response is not None

    # log the message and the answer in phospho
    phospho.log(
        input="Hello !",
        output=response.choices[0].message,
        user_id="Nico_le_plus_beau",
        metadata={"greetings": "Hello", "user message": "Hello"},
    )

    # Call the export analytics API
    response = requests.post(
        f"{backend_url}/api/v3/export/analytics",
        json={
            "pivot_query": {
                "project_id": project_id,
                "metric": "nb_messages",
                "metric_metadata": "greetings",
                "breakdown_by": "user message",
            }
        },
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200, response.reason
    assert response.json()["pivot_table"] is not None

    # Call the export users API
    response = requests.post(
        f"{backend_url}/api/v3/export/projects/{project_id}/users",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert response.status_code == 200, response.reason
    assert response.json() is not None

    # Delete project
    delete_project = requests.delete(
        f"{backend_url}/api/projects/{project_id}/delete",
        headers={"Authorization": f"Bearer {access_token}"},
    )
    assert delete_project.status_code == 200, delete_project.reason
