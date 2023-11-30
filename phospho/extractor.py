import logging
import pydantic

from typing import Union, Dict, Any, Tuple, Optional, Callable

from .utils import convert_to_jsonable_dict, generate_uuid

RawDataType = Union[Dict[str, Any], pydantic.BaseModel]

logger = logging.getLogger(__name__)


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
    """
    This function extracts from an arbitrary input the string representation, aka the prompt.
    """
    # OpenAI inputs: Look for messages list
    if (
        isinstance(input, dict)
        and ("messages" in input.keys())
        and isinstance(input["messages"], list)
        and (len(input["messages"]) > 0)
        and ("content" in input["messages"][-1])
    ):
        content = input["messages"][-1].get("content", None)
        if content is not None:
            return str(content)

    # Unimplemented. Translate everything to str
    return str(input)


def detect_task_id_and_to_log_from_output(
    output: RawDataType
) -> Tuple[Optional[str], bool]:
    """
    This function extracts from an arbitrary output an eventual task_id and to_log bool.
    task_id is used to grouped multiple outputs together.
    to_log is used to delay the call to the phospho API. Only logs marked as to_log will
    be recorded to phospho.
    This is useful to fully receive a streamed response before logging it to phospho.
    """
    output_class_name = output.__class__.__name__
    output_module = output.__class__.__module__
    logger.debug(
        f"Detecting task_id from output class_name:{output_class_name} ; module:{output_module}"
    )

    # OpenAI Stream API
    # task_id = ChatCompletionMessage.id
    # finish_reason = ChatCompletionMessage.choices[0].finish_reason
    if isinstance(output, pydantic.BaseModel) and (
        output_class_name == "ChatCompletionChunk"
    ):
        task_id = getattr(output, "id", None)
        choices = getattr(output, "choices", None)
        if isinstance(choices, list) and len(choices) > 0:
            # finish_reason is a str if completion has finished
            finish_reason = getattr(choices[0], "finish_reason", None)

        return task_id, (finish_reason is not None)
    # Unimplemented
    return None, True


def detect_str_from_output(output: RawDataType) -> str:
    """
    This function extracts from an arbitrary output its string representation.
    For example, from an OpenAI's ChatCompletion, extract the message displayed to the
    end user.
    """
    output_class_name = output.__class__.__name__
    output_module = output.__class__.__module__
    logger.debug(
        f"Detecting str from output class_name:{output_class_name} ; module:{output_module}"
    )

    # OpenAI outputs
    if isinstance(output, pydantic.BaseModel):
        if output_class_name in ["ChatCompletion", "ChatCompletionChunk"]:
            choices = getattr(output, "choices", None)
            if isinstance(choices, list) and len(choices) > 0:
                if output_class_name == "ChatCompletion":
                    # output = ChatCompletionMessage.choices[0].message.content
                    message = getattr(choices[0], "message", None)
                    content = getattr(message, "content", None)
                    if content is not None:
                        return str(content)
                elif output_class_name == "ChatCompletionChunk":
                    # new_token = ChatCompletionMessage.choices[0].delta.content
                    choice_delta = getattr(choices[0], "delta")
                    content = getattr(choice_delta, "content", None)
                    if content is not None:
                        return str(content)
                    else:
                        # None content = end of generation stream
                        return ""

    # Unimplemented. Translate everything to str
    return str(output)


def get_input_output(
    input: Union[RawDataType, str],
    output: Optional[Union[RawDataType, str]] = None,
    raw_input: Optional[RawDataType] = None,
    raw_output: Optional[RawDataType] = None,
    input_to_str_function: Optional[Callable[[Any], str]] = None,
    output_to_str_function: Optional[Callable[[Any], str]] = None,
    output_to_task_id_and_to_log_function: Optional[
        Callable[[Any], Tuple[Optional[str], bool]]
    ] = None,
    verbose: bool = True,
) -> Tuple[
    str,
    Optional[str],
    Optional[Union[Dict[str, object], str]],
    Optional[Union[Dict[str, object], str]],
    Optional[str],
    bool,
]:
    """
    Convert any supported data type to standard, loggable inputs and outputs.

    input: The input content to be logged. Can be a string, a dict, or a Pydantic model.
    output: The output content to be logged. Can be a string, a dict, a Pydantic model, or None.
    raw_input: Will be separately logged in raw_input_to_log if specified.
    raw_output: Will be separately logged in raw_output_to_log if specified.

    Returns:
    input_to_log (str): A string representation of the input.
    output_to_log (Optional[str]): A string representation of the output,
        or None if no output is specified.
    raw_input_to_log (Optional[Dict[str, object]]): A dict representation
        of the input, raw_input if specified, or None if input is a str.
    raw_output_to_log (Optional[Dict[str, object]]): A dict representation
        of the output, raw_output if specified, or None if output is a str.
    task_id_from_output (Optional[str]): Task id detected from the output. Useful from
        keeping track of streaming outputs.
    to_log (bool): Whether to log the event directly, or wait until a later event.
        Useful for streaming.
    """

    # Default functions to extract string from input and output
    if input_to_str_function is None:
        input_to_str_function = detect_str_from_input
    if output_to_str_function is None:
        output_to_str_function = detect_str_from_output
    if output_to_task_id_and_to_log_function is None:
        output_to_task_id_and_to_log_function = detect_task_id_and_to_log_from_output

    # To avoid mypy errors
    raw_input_to_log: Optional[Union[Dict[str, object], str]] = None
    raw_output_to_log: Optional[Union[Dict[str, object], str]] = None

    task_id_from_output = None
    to_log = True

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
            task_id_from_output, to_log = output_to_task_id_and_to_log_function(output)
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

    return (
        input_to_log,
        output_to_log,
        raw_input_to_log,
        raw_output_to_log,
        task_id_from_output,
        to_log,
    )
