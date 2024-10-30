from phospho.collection import Collection

from typing import Dict, Literal, Optional, List
from phospho.models import Task


class TaskEntity:
    def __init__(self, client, task_id: str, _content: Optional[dict] = None):
        self._client = client
        self._task_id = task_id
        self._content = _content

    @property
    def id(self):
        return self._task_id

    @property
    def content(self):
        """
        WARNING : can cause divergence with the server
        """
        if self._content is None:
            # Query the server
            response = self._client._get(f"/tasks/{self._task_id}")
            try:
                self._content = Task(**response.json())
            except TypeError:  # Keep dict
                self._content = response.json()

        return self._content

    def content_as_dict(self) -> dict:
        content = self.content
        if isinstance(content, Task):
            return content.model_dump()
        else:
            return content

    def refresh(self) -> None:
        """
        Refresh the content of the task from the server
        Done inplace
        """
        response = self._client._get(f"/tasks/{self._task_id}")
        self._content = response.json()

    def update(
        self,
        metadata: Optional[dict] = None,
        data: Optional[dict] = None,
        notes: Optional[str] = None,
        flag: Optional[Literal["success", "failure"]] = None,
        flag_source: Optional[str] = None,
    ):
        response = self._client._post(
            f"/tasks/{self._task_id}",
            payload={
                "metadata": metadata,
                "data": data,
                "notes": notes,
                "flag": flag,
                "flag_source": flag_source,
            },
        )
        return TaskEntity(
            client=self._client, task_id=self._task_id, _content=response.json()
        )


class TaskCollection(Collection):
    def get(self, task_id: str):
        """Get a task by id"""
        # TODO: add filters, limits and pagination

        response = self._client._get(f"/tasks/{task_id}")

        return TaskEntity(self._client, response.json()["id"], _content=response.json())

    def create(
        self,
        session_id: str,
        sender_id: str,
        input: str,
        output: str,
        additional_input: Optional[dict] = None,
        additional_output: Optional[dict] = None,
        data: Optional[dict] = None,
    ):
        """
        Create a task
        """
        payload: Dict[str, object] = {
            "session_id": session_id,
            "sender_id": sender_id,
            "input": input,
            "additional_input": additional_input or {},
            "output": output,
            "additional_output": additional_output or {},
            "data": data or {},
        }

        response = self._client._post("/tasks", payload=payload)

        return TaskEntity(self._client, response.json()["id"])

    def get_all(self) -> List[TaskEntity]:
        """Returns a list of all of the project tasks"""
        # TODO : Filters
        # TODO : Limit
        # TODO : Pagination

        response = self._client._post(
            f"/projects/{self._client._project_id()}/tasks",
        )
        return [
            TaskEntity(client=self._client, task_id=task["id"], _content=task)
            for task in response.json()["tasks"]
        ]
