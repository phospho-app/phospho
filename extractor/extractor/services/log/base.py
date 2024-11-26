from typing import List, Optional, Union, cast

from loguru import logger
from phospho.lab.utils import get_tokenizer, num_tokens_from_messages
from phospho.models import Task
from phospho.utils import filter_nonjsonable_keys, is_jsonable

from extractor.models.log import LogEventForTasks
from extractor.utils import generate_timestamp


def convert_additional_data_to_dict(
    data: Union[dict, str, list, None],
    default_key_name: str,
) -> Optional[dict]:
    """This conversion function is used so that the additional_input and additional_output are always a dict."""
    if isinstance(data, dict):
        # If it's already a dict, just return it
        return data
    elif isinstance(data, str):
        # If it's a string, return a dict with the default key name
        return {default_key_name: data}
    elif isinstance(data, list):
        # If it's a list, return a dict with the default key name
        return {default_key_name: data}
    else:
        # Otherwise, it's unsuported. Return None
        return None


def get_time_created_at(
    client_created_at: Optional[int], created_at: Optional[int]
) -> int:
    """
    By default, the created_at of the task is the one from the client
    The client can send us weird values. Take care of the most obvious ones:
    if negative or more than 24 hours in the future, set to current time
    """
    # If created_at is not None, use it
    if created_at is not None:
        client_created_at = created_at

    if client_created_at is None:
        return generate_timestamp()
    if (client_created_at < 0) or (
        client_created_at > generate_timestamp() + 24 * 60 * 60
    ):
        return generate_timestamp()
    return client_created_at


def get_nb_tokens_prompt_tokens(
    log_event: LogEventForTasks, model: Optional[str]
) -> int | None:
    """
    Returns the number of tokens in the prompt tokens, using
    different heuristics depending on the input type.
    """
    tokenizer = get_tokenizer(model)
    if isinstance(log_event.raw_input, dict):
        # Assume there is a key 'messages' (OpenAI-like input)
        try:
            if isinstance(log_event.raw_output, dict):
                usage = cast(dict, log_event.raw_output.get("usage", {}))
                if usage:
                    return usage.get("prompt_tokens", None)
            else:
                messages = log_event.raw_input.get("messages", [])
                if isinstance(messages, list) and all(
                    isinstance(x, dict) for x in messages
                ):
                    return num_tokens_from_messages(
                        messages,
                        model=model,
                        tokenizer=tokenizer,
                    )
        except Exception as e:
            logger.warning(
                f"Error in get_nb_tokens_prompt_tokens with model: {model}, {e}"
            )
    if isinstance(log_event.raw_input, list):
        if all(isinstance(x, str) for x in log_event.raw_input):
            # Handle the case where the input is a list of strings
            return sum(len(tokenizer.encode(cast(str, x))) for x in log_event.raw_input)
        if all(isinstance(x, dict) for x in log_event.raw_input):
            # Assume it's a list of messages
            return num_tokens_from_messages(
                cast(List[dict], log_event.raw_input),
                model=model,
                tokenizer=tokenizer,
            )
    # Encode the string input
    return len(tokenizer.encode(log_event.input))


def get_nb_tokens_completion_tokens(
    log_event: LogEventForTasks, model: Optional[str]
) -> int | None:
    """
    Returns the number of tokens in the completion tokens, using
    different heuristics depending on the output type.
    """
    try:
        if isinstance(log_event.raw_output, dict):
            # Assume there is a key 'choices' (OpenAI-like output)
            try:
                usage = cast(dict, log_event.raw_output.get("usage", {}))
                logger.debug(f"Usage: {usage}")
                if usage:
                    return usage.get("total_tokens", None)
                else:
                    generated_choices = log_event.raw_output.get("choices", [])
                    logger.debug(f"Generated choices: {generated_choices}")
                    if isinstance(generated_choices, list) and all(
                        isinstance(x, dict) for x in generated_choices
                    ):
                        generated_messages = [
                            choice.get("message", {}) for choice in generated_choices
                        ]
                        return num_tokens_from_messages(generated_messages, model=model)
            except Exception as e:
                logger.warning(
                    f"Error in get_nb_tokens_completion_tokens with model: {model}, {e}"
                )
                return None
        if isinstance(log_event.raw_output, list):
            raw_output_nonull = [x for x in log_event.raw_output if x is not None]
            # Assume it's a list of str
            if all(isinstance(x, str) for x in raw_output_nonull):
                tokenizer = get_tokenizer(model)
                return sum(
                    len(tokenizer.encode(cast(str, x))) for x in raw_output_nonull
                )
            # If it's a list of dict, assume it's a list of streamed chunks
            if all(isinstance(x, dict) for x in raw_output_nonull):
                return len(log_event.raw_output)
        if log_event.output is not None:
            tokenizer = get_tokenizer(model)
            return len(tokenizer.encode(log_event.output))
    except Exception as e:
        logger.error(
            f"Error in get_nb_tokens_completion_tokens with model: {model}, {e}"
        )

    return None


def collect_metadata(log_event: LogEventForTasks) -> dict:
    """
    Collect the metadata from the log event.
    - Add all unknown fields to the metadata
    - Filter non-jsonable values
    - Compute token count if not present
    """
    # Collect the metadata
    metadata = getattr(log_event, "metadata", {})
    if metadata is None:
        metadata = {}

    # Add all unknown fields to the metadata
    for key, value in log_event.model_dump().items():
        if (
            key not in metadata.keys()
            and key not in Task.model_fields.keys()
            and key not in ["raw_input", "raw_output"]
            and is_jsonable(value)
        ):
            metadata[key] = value
    # Filter non-jsonable values
    metadata = filter_nonjsonable_keys(metadata)

    # Compute token count
    model = metadata.get("model", None)
    if not isinstance(model, str):
        model = None

    if "prompt_tokens" not in metadata.keys():
        metadata["prompt_tokens"] = get_nb_tokens_prompt_tokens(log_event, model)

    if "completion_tokens" not in metadata.keys():
        metadata["completion_tokens"] = get_nb_tokens_completion_tokens(
            log_event, model
        )

    if "total_tokens" not in metadata.keys():
        # If prompt_tokens or completion_tokens are None, set total_tokens to None
        # This is the case when someone specifically sets prompt_tokens or completion_tokens to None
        if (
            metadata.get("prompt_tokens", 0) is None
            or metadata.get("completion_tokens", 0) is None
        ):
            metadata["total_tokens"] = None
        else:
            prompt_tokens = metadata.get("prompt_tokens", 0)
            completion_tokens = metadata.get("completion_tokens", 0)
            if not isinstance(prompt_tokens, int):
                prompt_tokens = 0
            if not isinstance(completion_tokens, int):
                completion_tokens = 0
            metadata["total_tokens"] = prompt_tokens + completion_tokens

    return metadata
