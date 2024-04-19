"""
Access sessions
"""

from phospho.collection import Collection

from phospho.tasks import TaskEntity

from typing import Optional, Dict


class Session:
    def __init__(self, client, session_id: str, _content: Optional[dict] = None):
        self._client = client
        self._session_id = session_id
        self._content = _content

    @property
    def id(self):
        return self._session_id

    @property
    def content(self):
        """
        WARNING : can cause divergence with the server
        """
        if self._content is None:
            # Query the server
            response = self._client._get(f"/sessions/{self._session_id}")
            self._content = response.json()

        return self._content

    def refresh(self):
        """
        Refresh the content of the session from the server
        Done inplace
        """
        response = self._client._get(f"/sessions/{self._session_id}")
        self._content = response.json()

    # def update(self, metadata: Optional[dict] = None, data: Optional[dict] = None):
    #     if metadata is None and data is None:
    #         raise ValueError(
    #             "You must provide either metadata or data to update a session"
    #         )

    #     payload = {
    #         "metadata": metadata or {},
    #         "data": data or {},
    #     }

    #     response = self._client._post(
    #         f"/sessions/{self._session_id}/update", payload=payload
    #     )

    #     return Session(self._client, response.json()["session_id"])

    def list_tasks(self):
        """
        Use a Generator? -> would enable streaming
        TODO : add filters, limits and pagination
        """
        response = self._client._post(f"/sessions/{self._session_id}/tasks")

        tasks_list = []

        for task_content in response.json()["tasks"]:
            tasks_list.append(
                TaskEntity(self._client, task_content["task_id"], _content=task_content)
            )

        return tasks_list


class SessionCollection(Collection):
    # Get a session
    def get(self, session_id: str):
        # TODO: add filters, limits and pagination

        response = self._client._get(f"/sessions/{session_id}")

        return Session(self._client, response.json()["id"], _content=response.json())

    # Get all sessions (filters can be applied) -> projects
    def list(self):
        print("project id :", self._client._project_id())

        response = self._client._get(f"/projects/{self._client._project_id()}/sessions")

        sessions_list = []

        for session_content in response.json()["sessions"]:
            sessions_list.append(
                Session(self._client, session_content["id"], _content=session_content)
            )

        return sessions_list

    # Create a session
    # TODO : return a session object, like what replicates does for predictions
    def create(self, data: Optional[Dict[str, object]] = None):
        payload = {
            "project_id": self._client._project_id(),
            "data": data or {},
        }

        response = self._client._post("/sessions", payload=payload)

        if response.status_code == 200:
            print(response.json())
            return Session(self._client, response.json()["id"])

        else:
            raise ValueError(f"Error creating session: {response.json()}")
