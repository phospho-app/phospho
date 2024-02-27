from pydantic import BaseModel

from typing import get_args, Literal


# Function to get all possible values for Literal fields
def get_literal_values(model_class: type) -> dict:
    """
    Fetch all the possible values for Literal fields in a pydantic model.

    Returns:
        dict: A dictionary with the field name as key and the possible values as a list.
    """
    # verify if model_class is a class inherited from BaseModel
    if not issubclass(model_class, BaseModel):
        raise ValueError(
            "model_class must be a class inherited from pydantic.BaseModel"
        )

    literal_fields = {}
    for field_name, field_type in model_class.__annotations__.items():
        if hasattr(field_type, "__origin__") and field_type.__origin__ is Literal:
            literal_fields[field_name] = get_args(field_type)
    return literal_fields
