"""
All the models stored in database.
"""

import datetime
from typing import Dict, List, Literal, Optional, Any, Union

from pydantic import BaseModel, Field, field_serializer

from phospho.utils import generate_timestamp, generate_uuid
import json


class Eval(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    created_at: int = Field(default_factory=generate_timestamp)
    project_id: str
    org_id: Optional[str] = None
    session_id: Optional[str] = None
    task_id: str
    # Flag to indicate if the task is success or failure
    value: Optional[Literal["success", "failure", "undefined"]]
    # The source of the event (either "user" or "phospho-{id}")
    source: str
    test_id: Optional[str] = None
    notes: Optional[str] = None
    task: Optional["Task"] = None


DetectionScope = Literal[
    "task",
    "session",
    "task_input_only",
    "task_output_only",
]

DetectionEngine = Literal[
    "llm_detection",
    "keyword_detection",
    "regex_detection",
]


class EventDefinition(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    created_at: int = Field(default_factory=generate_timestamp)
    event_name: str
    description: str
    webhook: Optional[str] = None
    webhook_headers: Optional[dict] = None
    detection_engine: DetectionEngine = "llm_detection"
    detection_scope: DetectionScope = "task"
    keywords: Optional[str] = None
    regex_pattern: Optional[str] = None
    job_id: Optional[str] = None  # Associated job id


class Event(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    created_at: int = Field(default_factory=generate_timestamp)
    # The name of the event (as defined in the project settings)
    event_name: str
    task_id: Optional[str] = None
    session_id: Optional[str] = None
    project_id: str
    org_id: Optional[str] = None
    # The webhook that was called (happened if the event was True and the webhook was set in settings)
    webhook: Optional[str] = None
    # The source of the event (either "user" or "phospho-{id}")
    source: str
    event_definition: Optional[EventDefinition] = None
    task: Optional["Task"] = None
    messages: Optional[List["Message"]] = Field(default_factory=list)


class Task(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    created_at: int = Field(default_factory=generate_timestamp)
    project_id: str
    org_id: Optional[str] = None
    session_id: Optional[str] = None
    input: str
    additional_input: Optional[dict] = Field(default_factory=dict)
    output: Optional[str] = None
    additional_output: Optional[dict] = Field(default_factory=dict)
    metadata: Optional[dict] = Field(default_factory=dict)
    data: Optional[dict] = Field(default_factory=dict)
    # Flag to indicate if the task is success or failure
    flag: Optional[str] = None  # Literal["success", "failure", "undefined"]
    last_eval: Optional[Eval] = None
    # Events are stored in a subcollection of the task document
    events: Optional[List[Event]] = Field(default_factory=list)
    # The environment is a label
    environment: str = Field(default="default environment")
    # Notes are a free text field that can be edited
    notes: Optional[str] = None
    # Testing
    test_id: Optional[str] = None
    # Topics : a list of topics
    topics: Optional[List[str]] = Field(default_factory=list)

    def preview(self):
        # Return a string representation of the input and output
        # This is used to display a preview of the task in the frontend
        if self.output is not None:
            return f"{self.input} -> {self.output}"
        else:
            return self.input

    @field_serializer("metadata")
    def serialize_metadata(self, metadata: dict, _info):
        return json.loads(json.dumps(metadata, default=str))


class Session(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    created_at: int = Field(default_factory=generate_timestamp)
    project_id: str
    org_id: Optional[str] = None
    metadata: Optional[dict] = None
    data: Optional[dict] = None
    # Notes are a free text field that can be edited
    notes: Optional[str] = None
    # preview contains the first few tasks of the session
    preview: Optional[str] = None
    # The environment is a label
    environment: str = "default environment"
    events: Optional[List[Event]] = Field(default_factory=list)
    tasks: Optional[List[Task]] = None
    # Session length is computed dynamically. It may be None if not computed
    session_length: Optional[int] = None

    @field_serializer("metadata")
    def serialize_metadata(self, metadata: dict, _info):
        return json.loads(json.dumps(metadata, default=str))


class ProjectSettings(BaseModel):
    events: Dict[str, EventDefinition] = Field(default_factory=dict)


class Project(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    created_at: int = Field(default_factory=generate_timestamp)
    project_name: str  # to validate this, use https://docs.pydantic.dev/latest/concepts/validators/
    org_id: str
    settings: ProjectSettings = Field(default_factory=ProjectSettings)
    user_id: Optional[str] = None


class Organization(BaseModel):
    id: str
    created_at: int  # UNIX timetamp in seconds
    name: str
    modified_at: int
    email: str  # Email for the organization -> relevant notifications
    status: str  # Status of the organization -> "active" or "inactive"
    type: str  # Type of the organization -> "beta"


class Test(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    project_id: str
    org_id: Optional[str] = None
    created_by: str
    created_at: int = Field(default_factory=generate_timestamp)
    last_updated_at: int
    terminated_at: Optional[int] = None
    status: Literal["started", "completed", "canceled"]
    summary: dict = Field(default_factory=dict)


ComparisonResults = Literal[
    "Old output is better",
    "New output is better",
    "Same quality",
    "Both are bad",
    "Error",
]


class Comparison(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    created_at: int = Field(default_factory=generate_timestamp)
    project_id: Optional[str] = None
    org_id: Optional[str] = None
    instructions: Optional[str] = None
    context_input: str
    old_output: str
    new_output: str
    comparison_result: ComparisonResults
    source: str
    test_id: Optional[str] = None


class LlmCall(BaseModel, extra="allow"):
    id: str = Field(default_factory=generate_uuid)
    org_id: Optional[str] = None
    created_at: int = Field(default_factory=generate_timestamp)
    model: str
    prompt: str
    llm_output: Optional[str] = None
    api_call_time: float  # In seconds
    # Identifier of the source of the evaluation, with the version of the model if phospho
    evaluation_source: Optional[str] = None
    task_id: Optional[str] = None
    session_id: Optional[str] = None
    job_id: Optional[str] = None


class FlattenedTask(BaseModel, extra="allow"):
    task_id: str
    task_input: Optional[str] = None
    task_output: Optional[str] = None
    task_metadata: Optional[dict] = None
    task_eval: Optional[Literal["success", "failure"]] = None
    task_eval_source: Optional[str] = None
    task_eval_at: Optional[int] = None
    task_created_at: Optional[int] = None
    session_id: Optional[str] = None
    session_length: Optional[int] = None
    event_name: Optional[str] = None
    event_created_at: Optional[int] = None


class DatasetRow(BaseModel, extra="allow"):
    id: str = Field(default_factory=generate_uuid)
    created_at: int = Field(default_factory=generate_timestamp)
    org_id: str
    detection_scope: DetectionScope
    task_input: str
    task_output: str
    event_description: str
    label: bool
    file_id: str  # Generated on the fly when the file is uploaded to the API
    file_name: str


class FineTuningJob(BaseModel, extra="allow"):
    id: str = Field(default_factory=lambda: generate_uuid("ftjob_"))
    created_at: int = Field(default_factory=generate_timestamp)
    org_id: str
    file_id: str  # File id used for the fine-tuning (will be splitted in train and validation sets)
    fine_tuned_model: Optional[
        str
    ] = None  # The name of the fine-tuned model that is being created. Null if the fine-tuning job is still running.
    finished_at: Optional[int] = None
    parameters: Optional[
        dict
    ] = {}  # Storing parameters for the fine-tuning job, also detection_scope, event_description
    model: str  # The base model that is being fine-tuned.
    status: Literal["started", "finished", "failed", "cancelled"]


class Message(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    created_at: int = Field(default_factory=generate_timestamp)
    role: Optional[str] = None
    content: str
    previous_messages: List["Message"] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

    def as_list(self):
        """
        Return the message and its previous messages as a list of Message objects.
        """
        if self.previous_messages:
            return self.previous_messages + [self]
        else:
            return [self]

    def transcript(
        self,
        with_role: bool = True,
        with_previous_messages: bool = False,
        only_previous_messages: bool = False,
    ) -> str:
        """
        Return a string representation of the message.
        """
        transcript = ""
        if with_previous_messages:
            transcript += "\n".join(
                [
                    message.transcript(with_role=with_role)
                    for message in self.previous_messages
                ]
            )
        if not only_previous_messages:
            if with_role:
                transcript += f"{self.role}: {self.content}"
            else:
                transcript += "\n" + self.content
        return transcript

    def previous_messages_transcript(
        self,
        with_role: bool = True,
    ) -> Optional[str]:
        """
        Return a string representation of the message.
        """
        if len(self.previous_messages) == 0:
            return None
        return self.transcript(
            with_role=with_role,
            with_previous_messages=True,
            only_previous_messages=True,
        )

    def latest_interaction(self) -> str:
        """
        Return the latest interaction of the message
        """
        # Latest interaction is the last message of the previous messages
        # And the message itself
        if len(self.previous_messages) == 0:
            return self.transcript(with_role=True)
        else:
            return "\n".join(
                [
                    self.previous_messages[-1].transcript(with_role=True),
                    self.transcript(with_role=True),
                ]
            )

    def latest_interaction_context(self) -> Optional[str]:
        """
        Return the context of the latest interaction, aka
        the n-2 previous messages until n-1 and message.
        """
        if len(self.previous_messages) <= 1:
            return None
        else:
            return "\n".join(
                [
                    message.transcript(with_role=True)
                    for message in self.previous_messages[:-1]
                ]
            )

    @classmethod
    def from_df(cls, df, **kwargs) -> List["Message"]:
        """
        Create a list of Message objects from a pandas DataFrame.

        ```python
        import pandas as pd

        df = pd.DataFrame({
            "content": ["Hello", "How are you?"],
            "context_role": ["user", "assistant"],
        })

        messages = Message.from_df(df, role="context_role)
        ```

        :param df: The DataFrame to convert to a list of Message objects
        :param kwargs: The mapping from the Message fields to the column names of the DataFrame.
            Supported fields are: id, created_at, role, content, previous_messages, metadata.
            - The only required field is "content". Other fields are optional.
            - If not provided, a default mapping is used, where the field name is the same as the column name.
            - If the mapping refers to an unknown column name, a ValueError is raised.
            - Pass None to a field to skip it and use a default value.

        :return: A list of Message objects
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("Pandas is required to use the from_df method")

        # The keyword arguments are understood as mapping from the Message
        # fields to the column names of the DataFrame
        # If not provided, the default mapping is used
        default_mapping: Dict[str, object] = {
            "id": None,
            "created_at": "created_at",
            "role": "role",
            "content": "content",
            "previous_messages": "previous_messages",
            "metadata": "metadata",
        }
        # If a default mapping value is not found in the DataFrame, it is skipped
        for key, value in default_mapping.items():
            if value not in df.columns:
                default_mapping[key] = None
        # If a kwargs refers to an unknwon column name, raise a ValueError
        for key, value in kwargs.items():
            if value not in df.columns and value is not None:
                raise ValueError(f"Column {value} not found in the DataFrame")

        col_mapping = {**default_mapping, **kwargs}

        # Verify that mandatory field are present. If not, raise a ValueError
        if col_mapping["content"] is None:
            raise ValueError(
                f'Column "content" not found in the DataFrame. '
                + 'Please provide a keyword argument with the column to use: `Message.from_df(df, content="message_content")`.'
            )

        # Convert every row of the df into a lab.Message
        messages = []
        for index, row in df.iterrows():
            content = row[col_mapping["content"]]
            if content and not pd.isnull(content):
                values_to_create_message = {}
                for attribute, col_name in col_mapping.items():
                    if col_name is not None:
                        values_to_create_message[attribute] = row[col_name]
                if col_mapping["id"] is None:
                    # By default, the id is the index of the row
                    message_id = str(index)
                else:
                    message_id = row[col_mapping["id"]]
                message_dict = {
                    **values_to_create_message,
                    "id": message_id,
                    "content": content,
                }
                messages.append(cls(**message_dict))

        return messages

    @classmethod
    def from_task(
        cls,
        task: Task,
        previous_tasks: Optional[List[Task]] = None,
        metadata: Optional[dict] = None,
    ) -> "Message":
        """
        Create a Message from a Task object.

        The Message object is created from the input and output of the Task object.
        If the Task object has previous tasks, the Message object will contain
        the input and output of the previous tasks as well.

        :return: A list of Message objects
        """
        if metadata is None:
            metadata = {}
        if previous_tasks is None:
            previous_tasks = []

        previous_messages: List["Message"] = []
        for i, previous_task in enumerate(previous_tasks):
            previous_messages.append(
                cls(
                    id="input_" + previous_task.id,
                    role="User",
                    content=previous_task.input,
                )
            )
            if previous_task.output is not None:
                previous_messages.append(
                    cls(
                        id="output_" + previous_task.id,
                        role="Assistant",
                        content=previous_task.output,
                    )
                )

        if task.output is not None:
            previous_messages.append(
                cls(
                    id="input_" + task.id,
                    role="User",
                    content=task.input,
                )
            )
            message = cls(
                id="output_" + task.id,
                role="Assistant",
                content=task.output,
                previous_messages=previous_messages,
                metadata=metadata,
            )
        else:
            message = cls(
                id="input_" + task.id,
                role="User",
                content=task.input,
                previous_messages=previous_messages,
                metadata=metadata,
            )

        return message

    @classmethod
    def from_session(
        cls, session: Session, metadata: Optional[dict] = None
    ) -> "Message":
        """
        Create a list of Message objects from a Session object.

        :param session: The Session object to convert to a list of Message objects

        :return: A list of Message objects
        """
        if session.tasks is None or len(session.tasks) == 0:
            raise ValueError("The session does not contain any task")
        task = session.tasks[-1]
        if len(session.tasks) == 1:
            previous_tasks = []
        else:
            previous_tasks = session.tasks[:-1]
        return cls.from_task(
            task=task, previous_tasks=previous_tasks, metadata=metadata
        )


JobType = Literal["evaluation", "event_detection"]  # Add other job types here


class Job(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    created_at: int = Field(default_factory=generate_timestamp)
    org_id: str
    project_id: str
    status: Literal["enabled", "deleted"]
    job_type: JobType
    parameters: dict = Field(
        default_factory=dict
    )  # Parameters for the job, for instance it was the event object in the settings


class Prediction(BaseModel):
    """
    Represents a prediction made by phospho, the user or else
    For instance, a user feedback as "Failure" is a prediction
    For instance, the output of an event detection is a prediction
    """

    id: str = Field(default_factory=generate_uuid)
    created_at: int = Field(default_factory=generate_timestamp)
    org_id: str
    project_id: str
    job_type: JobType
    job_id: str  # The id of the job that generated the prediction
    value: Any  # The value of the prediction


class ProjectDataFilters(BaseModel):
    """
    This is a model used to filter tasks, sessions or events in
    different endpoints.
    """

    created_at_start: Optional[Union[int, datetime.datetime]] = None
    created_at_end: Optional[Union[int, datetime.datetime]] = None
    event_name: Optional[List[str]] = None
    flag: Optional[str] = None
    metadata: Optional[dict] = None
    user_id: Optional[str] = None
    last_eval_source: Optional[str] = None
