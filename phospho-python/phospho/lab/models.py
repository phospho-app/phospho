import itertools
import logging
from enum import Enum
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field

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


class ResultType(Enum):
    error = "error"
    bool = "bool"
    literal = "literal"


class JobResult(BaseModel, extra="allow"):
    created_at: int = Field(default_factory=generate_timestamp)
    job_id: str
    result_type: ResultType
    value: Any
    logs: List[Any] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)


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
