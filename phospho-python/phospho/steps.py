from phospho.collection import Collection

from typing import Optional


class Step:
    def __init__(self, client, step_id: str, _content: Optional[dict] = None):
        self._client = client
        self._step_id = step_id
        self._content = _content

    @property
    def id(self):
        return self._step_id

    @property
    def content(self):
        """
        WARNING : can cause divergence with the server
        """
        if self._content is None:
            # Query the server
            response = self._client._get(f"/steps/{self._step_id}")
            # Cache the data in the object
            self._content = response.json()

        return self._content

    def refresh(self):
        """
        Refresh the content of the step from the server
        Done inplace
        """
        response = self._client._get(f"/steps/{self._step_id}")
        self._content = response.json()

    def update(
        self,
        status: Optional[str] = None,
        is_last: Optional[bool] = None,
        output: Optional[str] = None,
        additional_output: Optional[dict] = None,
        metadata: Optional[dict] = None,
        data: Optional[dict] = None,
    ):
        # Create a dictionary comprehension to filter out non-None arguments
        update_data = {
            "status": status,
            "is_last": is_last,
            "output": output,
            "additional_output": additional_output,
            "metadata": metadata,
            "data": data,
        }

        # Use a dictionary comprehension to exclude keys with None values
        payload = {
            key: value for key, value in update_data.items() if value is not None
        }

        print(payload)

        if not payload:
            raise ValueError("You must provide at least one argument to update a step")

        response = self._client._post(f"/steps/{self._step_id}/update", payload=payload)

        return Step(self._client, response.json()["step_id"])


class StepCollection(Collection):
    # Get a Step
    def get(self, step_id: str):
        # TODO: add filters, limits and pagination

        response = self._client._get(f"/steps/{step_id}")

        return Step(self._client, response.json()["id"], _content=response.json())

    # Get all sessions (filters can be applied) -> projects

    # Create a session
    # TODO : return a session object, like what replicates does for predictions
    def create(
        self,
        task_id: str,
        input: str,
        name: str,
        status: str,
        is_last: bool,
        additional_input: Optional[dict] = None,
        data: Optional[dict] = None,
    ):
        payload = {
            "task_id": task_id,
            "input": input,
            "name": name,
            "status": status,
            "is_last": is_last,
            "additional_input": additional_input or {},
            "data": data or {},
        }

        response = self._client._post(f"/steps", payload=payload)

        return Step(self._client, response.json()["step_id"])


# Get all tasks (filters can be applied)

# Create a task

# Update a task

# Get the all steps for a task
