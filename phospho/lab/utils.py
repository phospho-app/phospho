from .models import JobConfig
from typing import List
import itertools

from typing import get_args, Literal


# Function to get all possible values for Literal fields
def get_literal_values(model_class):
    literal_fields = {}
    for field_name, field_type in model_class.__annotations__.items():
        if hasattr(field_type, "__origin__") and field_type.__origin__ is Literal:
            literal_fields[field_name] = get_args(field_type)
    return literal_fields


def generate_configurations(
    job_config: JobConfig, exclude_default: bool = True
) -> List[JobConfig]:
    """
    Generate all the possible configurations from a job config

    :param job_config: The job config to generate the configurations from
    :param exclude_default: Whether to exclude the default configuration
    """
    # Get all possible values for the JobConfig model
    literal_values = get_literal_values(job_config)

    # Generate all possible combinations of Literal values
    all_combinations = list(itertools.product(*literal_values.values()))

    # Exclude the combination that matches the default configuration
    if exclude_default:
        default_values = tuple(
            getattr(job_config, field) for field in literal_values.keys()
        )
        combinations = [combo for combo in all_combinations if combo != default_values]
    else:
        combinations = all_combinations

    # Create a list of JobConfig objects with all possible combinations
    config_objects = [
        job_config.__class__(**dict(zip(literal_values.keys(), combo)))
        for combo in combinations
    ]

    return config_objects
