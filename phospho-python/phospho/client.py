"""
phospho client to interact with the phospho API
"""

import os
from typing import Dict, List, Literal, Optional

import requests

import phospho.config as config

from phospho.sessions import SessionCollection
from phospho.tasks import TaskCollection, TaskEntity
from phospho.models import Comparison, Task, Test, FlattenedTask, Project


class Client:
    """Standard client for calls to the phospho backend"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        self.api_key = api_key
        self.project_id = project_id
        # If no api_key is provided, verify that there is an environment variable
        if not api_key:
            self._api_key()
        # If no project_id is provided, verify that there is an environment variable
        if not project_id:
            self._project_id()

        if not base_url:
            self.base_url = config.BASE_URL
        else:
            self.base_url = base_url

    def _api_key(self) -> str:
        token = self.api_key
        # Evaluate lazily in case environment variable is set with dotenv, or something
        if token is None:
            token = os.environ.get("PHOSPHO_API_KEY")
        if not token:
            raise ValueError(
                "No API key provided. You need to set the PHOSPHO_API_KEY environment variable or init phospho with"
                + " `phospho.init(api_key=...)`.\n\nFind your API key on https://platform.phospho.ai in Settings"
            )
        return token

    def _project_id(self) -> str:
        project_id = self.project_id
        # Evaluate lazily in case environment variable is set with dotenv, or something
        if project_id is None:
            project_id = os.environ.get("PHOSPHO_PROJECT_ID")
        if not project_id:
            raise ValueError(
                "No project id provided. You need to set the PHOSPHO_PROJECT_ID environment"
                + " variable or init phospho with `phospho.init(project_id=...)`.\n\n"
                + "Find your project id on https://platform.phospho.ai in Settings"
            )
        return project_id

    def _headers(self) -> Dict[str, str]:
        # TODO : "User-Agent": f"replicate-python/{__version__}",
        return {
            "Authorization": f"Bearer {self._api_key()}",
            "content-type": "application/json",
            "accept": "application/json",
        }

    def _get(
        self, path: str, params: Optional[Dict[str, str]] = None
    ) -> requests.Response:
        url = f"{self.base_url}{path}"
        response = requests.get(url, headers=self._headers(), params=params)

        if response.status_code >= 200 and response.status_code < 300:
            return response

        else:
            try:
                json = response.json()
                raise ValueError(
                    f"Error posting {url} (code: {response.status_code}): {json}"
                )
            except Exception as e:
                raise ValueError(
                    f"Error posting {url} (code: {response.status_code}): {response.text}"
                )

    def _post(
        self, path: str, payload: Optional[Dict[str, object]] = None
    ) -> requests.Response:
        url = f"{self.base_url}{path}"
        response = requests.post(url, headers=self._headers(), json=payload)

        if response.status_code >= 200 and response.status_code < 300:
            return response
        else:
            try:
                json = response.json()
                raise ValueError(
                    f"Error posting {url} (code: {response.status_code}): {json}"
                )
            except Exception as e:
                raise ValueError(
                    f"Error posting {url} (code: {response.status_code}): {response.text}"
                )

    @property
    def sessions(self) -> SessionCollection:
        """Return a SessionCollection to interact with the sessions of the project"""
        return SessionCollection(client=self)

    @property
    def tasks(self) -> TaskCollection:
        """Return a TaskCollection to interact with the tasks of the project"""
        return TaskCollection(client=self)

    def compare(
        self,
        context_input: str,
        old_output: str,
        new_output: str,
        test_id: Optional[str] = None,
    ) -> Comparison:
        """
        Compare the old and new answers to the context_input with an LLM
        """
        comparison_result = self._post(
            "/evals/compare",
            payload={
                "project_id": self._project_id(),
                "context_input": context_input,
                "old_output": old_output,
                "new_output": new_output,
                "test_id": test_id,
            },
        )

        return Comparison.model_validate(comparison_result.json())

    def flag(
        self,
        task_id: str,
        flag: Literal["success", "failure"],
        source: str = "user",
        notes: Optional[str] = None,
    ) -> TaskEntity:
        """
        Flag a task as a success or a failure. Returns the task.
        """

        response = self._post(
            f"/tasks/{task_id}/flag",
            payload={
                "flag": flag,
                "source": source,
                "notes": notes,
            },
        )
        return TaskEntity(client=self, task_id=task_id, _content=response.json())

    def create_test(self, summary: Optional[dict] = None) -> Test:
        """
        Start a test
        """

        response = self._post(
            "/tests",
            payload={
                "project_id": self._project_id(),
                "summary": summary,
            },
        )
        return Test(**response.json())

    def update_test(
        self, test_id: str, status: Literal["completed", "canceled"]
    ) -> Test:
        """
        Update a test
        """

        response = self._post(
            f"/tests/{test_id}",
            payload={
                "status": status,
            },
        )
        return Test(**response.json())

    def tasks_flat(
        self,
        limit: int = 1000,
        with_events: bool = True,
        with_sessions: bool = True,
    ) -> dict:
        """
        Get the tasks of a project in a flattened format.
        """

        response = self._post(
            f"/projects/{self._project_id()}/tasks/flat",
            payload={
                "limit": limit,
                "with_events": with_events,
                "with_sessions": with_sessions,
            },
        )
        return response.json()

    def update_tasks_flat(self, flattened_tasks: List[FlattenedTask]) -> None:
        """
        Update the tasks of a project using a flattened format.
        """

        self._post(
            f"/projects/{self._project_id()}/tasks/flat-update",
            payload={
                "flattened_tasks": [task.model_dump() for task in flattened_tasks]
            },
        )
        return None

    def project_config(self) -> Project:
        """
        Get the project configuration and settings
        """

        response = self._get(f"/projects/{self._project_id()}")
        return Project.model_validate(response.json())

    def backfill(self, tasks: List[Task]) -> None:
        """
        Upload historical data in batch to phospho to backfill the logs.
        For now, this doesn't send the task in the main_pipeline()
        """
        # Assert that all tasks have a created_at timestamp, otherwise the backend won't store them
        for task in tasks:
            if task.created_at is None:
                raise ValueError(
                    f"Task {task.id} has no created_at timestamp. All tasks must have a created_at timestamp when backfilling data"
                )

        self._post(
            f"/log/{self._project_id()}",
            payload={"batched_log_events": [task.model_dump() for task in tasks]},
        )

        return None
