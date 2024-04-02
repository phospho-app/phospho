import itertools
import logging
from enum import Enum
from typing import Any, List, Literal, Optional

from pydantic import BaseModel, Field

from phospho.models import (
    EventDefinition,
    Project,
    Task,
    Session,
    DetectionScope,
    Message,
)
from phospho.utils import generate_timestamp

from .utils import get_literal_values

logger = logging.getLogger(__name__)


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
