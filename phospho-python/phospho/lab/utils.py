import logging
from pydantic import BaseModel

from typing import List, Optional, get_args, Literal

logger = logging.getLogger(__name__)


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


try:
    import tiktoken

    def get_tokenizer(model: Optional[str]) -> tiktoken.Encoding:
        if model is None:
            return tiktoken.get_encoding("cl100k_base")
        try:
            return tiktoken.encoding_for_model(model)
        except KeyError:
            return tiktoken.get_encoding("cl100k_base")

    def num_tokens_from_messages(
        messages: List[dict],
        model: Optional[str] = "gpt-3.5-turbo-0613",
        tokenizer=None,
    ):
        """
        Return the number of tokens used by a list of messages.

        https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb
        """
        if tokenizer is None:
            tokenizer = get_tokenizer(model)
        if model is None:
            model = "gpt-3.5-turbo"
        if model in {
            "gpt-3.5-turbo-0613",
            "gpt-3.5-turbo-16k-0613",
            "gpt-4-0314",
            "gpt-4-32k-0314",
            "gpt-4-0613",
            "gpt-4-32k-0613",
        }:
            tokens_per_message = 3
            tokens_per_name = 1
        elif model == "gpt-3.5-turbo-0301":
            tokens_per_message = (
                4  # every message follows <|start|>{role/name}\n{content}<|end|>\n
            )
            tokens_per_name = -1  # if there's a name, the role is omitted
        elif "gpt-3.5-turbo" in model:
            logger.debug(
                "Warning: gpt-3.5-turbo may update over time. Returning num tokens assuming gpt-3.5-turbo-0613."
            )
            tokens_per_message = 3
            tokens_per_name = 1
        elif "gpt-4" in model:
            logger.debug(
                "Warning: gpt-4 may update over time. Returning num tokens assuming gpt-4-0613."
            )
            tokens_per_message = 3
            tokens_per_name = 1
        else:
            logger.warning(
                f"""num_tokens_from_messages() is not implemented for model {model}. See https://github.com/openai/openai-python/blob/main/chatml.md for information on how messages are converted to tokens."""
            )
            tokens_per_message = 3
            tokens_per_name = 1
        num_tokens = 0
        for message in messages:
            num_tokens += tokens_per_message
            for key, value in message.items():
                num_tokens += len(tokenizer.encode(value))
                if key == "name":
                    num_tokens += tokens_per_name
        num_tokens += 3  # every reply is primed with <|start|>assistant<|message|>
        return num_tokens

except ImportError:
    pass
