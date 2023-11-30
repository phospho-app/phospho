"""
phospho client to interact with the phospho API

TODO
- Add support for pagination and filters
- Add support for retrying requests and handling rate limits
- Add support for AsyncIO -> be non blocking in the background
"""
import os
from typing import Dict, Optional

import requests

import phospho.config as config

from phospho.sessions import SessionCollection
from phospho.tasks import TaskCollection
from phospho.steps import StepCollection


class Client:
    """This is a class to standardize calls to the phospho backend"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        base_url: Optional[str] = None,
    ) -> None:
        self.api_key = api_key
        self.project_id = project_id
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
                "No API key provided. You need to set the PHOSPHO_API_KEY environment variable or create"
                + " a client with `phospho.Client(api_key=...)`.\n\nFind your API key on https://phospho.app"
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
                + " variable or create a client with `phospho.Client(project_id=...)`."
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
            raise ValueError(f"Error getting {url}: {response.json()}")

    def _post(
        self, path: str, payload: Optional[Dict[str, object]] = None
    ) -> requests.Response:
        url = f"{self.base_url}{path}"
        response = requests.post(url, headers=self._headers(), json=payload)

        if response.status_code >= 200 and response.status_code < 300:
            return response

        else:
            raise ValueError(f"Error posting to {url}: {response.json()}")

    @property
    def sessions(self) -> SessionCollection:
        return SessionCollection(client=self)

    @property
    def tasks(self) -> TaskCollection:
        return TaskCollection(client=self)

    # @property
    # def steps(self) -> StepCollection:
    #     return StepCollection(client=self)
