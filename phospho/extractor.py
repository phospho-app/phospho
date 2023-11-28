import pydantic

from typing import Union, Dict, Any, Tuple, Optional, Callable

from .utils import convert_to_jsonable_dict

RawDataType = Union[Dict[str, Any], pydantic.BaseModel]


def convert_to_dict(x: Any) -> Dict[str, object]:
    """Convert objects to a dict, ideally json serializable."""
    if isinstance(x, dict):
        return x
    elif isinstance(x, pydantic.BaseModel):
        return x.model_dump()
    else:
        try:
            return dict(x)
        except ValueError as e:
            raise NotImplementedError(
                f"Dict conversion not implemented for type {type(x)}: {x}"
            )


def detect_str_from_input(input: RawDataType) -> str:
    # OpenAI inputs: Look for messages list
    if (
        isinstance(input, dict)
        and ("messages" in input.keys())
        and isinstance(input["messages"], list)
        and (len(input["messages"]) > 0)
        and ("content" in input["messages"][-1])
    ):
        role = input["messages"][-1].get("role", None)
        content = input["messages"][-1].get("content", None)
        if role is not None and content is not None:
            return str(content) # Should we really add the role?
        elif content is not None:
            return str(content)

    # Unimplemented. Translate everything to str
    return str(input)


def detect_str_from_output(output: RawDataType) -> str:
    # OpenAI outputs
    # output = ChatCompletionMessage.choices[0].message.content
    if (
        isinstance(output, pydantic.BaseModel)
        and ("choices" in output.model_fields.keys())
        and isinstance(getattr(output, "choices", [None])[0], pydantic.BaseModel)
    ):
        choices = getattr(output, "choices", None)
        if isinstance(choices, list) and len(choices) > 0:
            message = getattr(choices[0], "message", None)
            if isinstance(message, pydantic.BaseModel):
                role = getattr(message, "role", None)
                content = getattr(message, "content", None)
                if role is not None and content is not None:
                    return f"{role}: {content}"
                elif content is not None:
                    return str(content)

    # Unimplemented. Translate everything to str
    return str(output)


def get_input_output(
    input: Union[RawDataType, str],
    output: Optional[Union[RawDataType, str]],
    raw_input: Optional[RawDataType],
    raw_output: Optional[RawDataType],
    input_to_str_function: Optional[Callable[[Any], str]],
    output_to_str_function: Optional[Callable[[Any], str]],
    verbose: bool = True,
) -> Tuple[
    str,
    Optional[str],
    Optional[Union[Dict[str, object], str]],
    Optional[Union[Dict[str, object], str]],
]:
    """
    Convert any supported data type to standard, loggable inputs and outputs.

    input (Union[RawDataType, str]): The input content to be logged. Can
        be a string, a dict, or a Pydantic model.
    output (Optional[Union[RawDataType, str]], default None): The output
        content to be logged. Can be a string, a dict, a Pydantic model, or None.
    raw_input (Optional[RawDataType], default None): Will be separately logged
        in raw_input_to_log if specified.
    raw_output (Optional[RawDataType], default None): Will be separately logged
        in raw_output_to_log if specified.

    Returns:
    input_to_log (str): A string representation of the input.
    output_to_log (Optional[str]): A string representation of the output,
        or None if no output is specified.
    raw_input_to_log (Optional[Dict[str, object]]): A dict representation
        of the input, raw_input if specified, or None if input is a str.
    raw_output_to_log (Optional[Dict[str, object]]): A dict representation
        of the output, raw_output if specified, or None if output is a str.
    """

    # Default functions to extract string from input and output
    if input_to_str_function is None:
        input_to_str_function = detect_str_from_input
    if output_to_str_function is None:
        output_to_str_function = detect_str_from_output

    # To avoid mypy errors
    raw_input_to_log: Optional[Union[Dict[str, object], str]] = None
    raw_output_to_log: Optional[Union[Dict[str, object], str]] = None

    # Extract a string representation from input
    if isinstance(input, str):
        input_to_log = input
        raw_input_to_log = input
    else:
        # Extract input str representation from input
        input_to_log = input_to_str_function(input)
        raw_input_to_log = convert_to_jsonable_dict(
            convert_to_dict(input), verbose=verbose
        )

    # If raw input is specified, override
    if raw_input is not None:
        raw_input_to_log = convert_to_jsonable_dict(
            convert_to_dict(raw_input), verbose=verbose
        )

    if output is not None:
        # Extract a string representation from output
        if isinstance(output, str):
            output_to_log = output
            raw_output_to_log = output
        else:
            output_to_log = output_to_str_function(output)
            raw_output_to_log = convert_to_jsonable_dict(
                convert_to_dict(output), verbose=verbose
            )
    else:
        output_to_log = None

    # If raw output is specified, override
    if raw_output is not None:
        raw_output_to_log = convert_to_jsonable_dict(
            convert_to_dict(raw_output), verbose=verbose
        )

    return input_to_log, output_to_log, raw_input_to_log, raw_output_to_log
