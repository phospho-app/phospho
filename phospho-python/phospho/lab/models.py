import itertools
import logging
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field

from phospho.models import EventDefinition, Project, Task, Session, DetectionScope
from phospho.utils import generate_timestamp, generate_uuid

from .utils import get_literal_values

logger = logging.getLogger(__name__)


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
            return [self.previous_messages, self]
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


class ResultType(Enum):
    error = "error"
    bool = "bool"
    literal = "literal"
    list = "list"
    dict = "dict"
    string = "string"
    number = "number"
    object = "object"


class JobResult(BaseModel, extra="allow"):
    value: Any
    result_type: ResultType
    logs: List[Any] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
    created_at: int = Field(default_factory=generate_timestamp)
    job_id: Optional[str] = None


class JobConfig(BaseModel, extra="allow"):
    """
    Custom configuration class for our implementation of the lab
    If you wish not to use any config, you can use the EmptyConfig class
    You need to pass default values for each parameter
    """

    def generate_configurations(
        self, exclude_default: bool = True
    ) -> List["JobConfig"]:
        """
        Generate all the possible configurations from a job config

        :param job_config: The job config to generate the configurations from
        :param exclude_default: Whether to exclude the default configuration
        """
        # Get all possible values for the JobConfig model
        literal_values = get_literal_values(self.__class__)
        # Generate all possible combinations of Literal values
        all_combinations = list(itertools.product(*literal_values.values()))

        # Exclude the combination that matches the default configuration
        if exclude_default:
            default_values = tuple(
                getattr(self, field) for field in literal_values.keys()
            )
            combinations = [
                combo for combo in all_combinations if combo != default_values
            ]
        else:
            combinations = all_combinations

        # Create a list of JobConfig objects with all possible combinations
        config_objects = []
        for combo in combinations:
            config_as_dict = self.model_dump()
            config_as_dict.update(dict(zip(literal_values.keys(), combo)))
            config_objects.append(self.__class__(**config_as_dict))

        return config_objects


### CUSTOM MODELS ##


class EventDetectionConfig(JobConfig):
    model: Literal["gpt-4", "gpt-3.5-turbo"] = "gpt-4"  # OpenAI model name
    # instruction: str


class EvalConfig(JobConfig):
    model: Literal["gpt-4", "gpt-3.5-turbo"] = "gpt-4"  # OpenAI model name
    metadata: dict = Field(default_factory=dict)


class EventConfig(JobConfig):
    event_name: str
    event_description: str
    event_scope: DetectionScope
