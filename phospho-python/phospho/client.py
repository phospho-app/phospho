"""
phospho client to interact with the phospho API
"""

import logging
import os
from typing import Dict, List, Literal, Optional

import requests

import phospho.config as config
from phospho.models import (
    FlattenedTask,
    Project,
    Task,
    ProjectDataFilters,
)
from phospho.sessions import SessionCollection
from phospho.tasks import TaskCollection, TaskEntity

logger = logging.getLogger(__name__)


class PhosphoServerSideError(Exception):
    pass


class PhosphoClientSideError(Exception):
    pass


class Client:
    """Standard client for calls to the phospho backend"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        self.__api_key = api_key
        self.__project_id = project_id
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
        token = self.__api_key
        # Evaluate lazily in case environment variable is set with dotenv, or something
        if token is None:
            token = os.environ.get("PHOSPHO_API_KEY")
        if not token:
            raise ValueError(
                "No API key provided. You need to set the PHOSPHO_API_KEY environment variable or init phospho with"
                + " `phospho.init(api_key=...)`.\n\nFind your API key on https://platform.phospho.ai in Settings"
            )
        return token

    def _displayable_api_key(self) -> str:
        """
        Display the first few characters of the API key
        """
        api_key = self._api_key()
        if api_key and len(api_key) > 5:
            first_few_chars = api_key[:5] + "..."
        elif api_key:
            first_few_chars = "***"
        else:
            first_few_chars = "None"
        return first_few_chars

    def _project_id(self) -> str:
        project_id = self.__project_id
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

    @property
    def project_id(self) -> str:
        return self._project_id()

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
        elif response.status_code >= 400 and response.status_code < 500:
            raise PhosphoClientSideError(
                f"Client-side error {response.status_code} GET {url}: {response.text}"
            )
        elif response.status_code >= 500:
            raise PhosphoServerSideError(
                f"Server-side error {response.status_code} GET {url}: {response.text}"
            )
        else:
            raise ValueError(
                f"Unknwon error {response.status_code} GET {url}: {response.text}"
            )

    def _post(
        self, path: str, payload: Optional[Dict[str, object]] = None
    ) -> requests.Response:
        url = f"{self.base_url}{path}"
        response = requests.post(url, headers=self._headers(), json=payload)

        if response.status_code >= 200 and response.status_code < 300:
            return response
        elif response.status_code >= 400 and response.status_code < 500:
            raise PhosphoClientSideError(
                f"Error {response.status_code} POST {url} with API key {self._displayable_api_key()} : {response.text}."
                + "\nThere is likely an issue with your config. Make sure you have the correct API key and project id: https://platform.phospho.ai"
            )
        elif response.status_code >= 500:
            raise PhosphoServerSideError(
                f"Error {response.status_code} POST {url}: {response.text}"
            )
        else:
            raise ValueError(
                f"Uknown error {response.status_code} POST {url}: {response.text}"
            )

    @property
    def sessions(self) -> SessionCollection:
        """Return a SessionCollection to interact with the sessions of the project"""
        return SessionCollection(client=self)

    @property
    def tasks(self) -> TaskCollection:
        """Return a TaskCollection to interact with the tasks of the project"""
        return TaskCollection(client=self)

    def flag(
        self,
        task_id: str,
        flag: Literal["success", "failure"],
        notes: Optional[str] = None,
        **kwargs,
    ) -> TaskEntity:
        """
        Flag a task as a success or a failure. Returns the task.
        """

        response = self._post(
            f"/tasks/{task_id}/human-eval",
            payload={
                "human_eval": flag,
                "project_id": self._project_id(),
                "source": "user",
                "notes": notes,
            },
        )
        return TaskEntity(client=self, task_id=task_id, _content=response.json())

    def fetch_tasks(self, filters: Optional[ProjectDataFilters] = None) -> List[Task]:
        """
        Get the tasks of a project.
        """
        if filters is None:
            filters = ProjectDataFilters()
        response = self._post(
            f"/projects/{self._project_id()}/tasks",
            payload={
                "filters": filters.model_dump(),
            },
        )
        return [Task.model_validate(task) for task in response.json()["tasks"]]

    def tasks_flat(
        self,
        limit: int = 1000,
        with_events: bool = True,
        with_sessions: bool = True,
        with_removed_events: bool = False,
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
                "with_removed_events": with_removed_events,
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

    def train(
        self, model: str, examples: list, task_type: str = "binary-classification"
    ) -> None:
        """
        Upload historical data in batch to phospho to backfill the logs.
        For now, this doesn't send the task in the main_pipeline()
        """
        # Assert that all tasks have a created_at timestamp, otherwise the backend won't store them

        assert task_type in ["binary-classification"], "Task type not supported"
        assert len(examples) >= 20, "You need at least 20 examples to train the model."

        response = self._post(
            "/train",
            payload={"model": model, "examples": examples, "task_type": task_type},
        )

        # Get the body of the response
        response_body = response.json()

        return response_body
