import os
from typing import Literal, Tuple

import phospho.config as config

try:
    from openai import AsyncOpenAI, OpenAI

except ImportError:
    AsyncOpenAI = OpenAI = object


def get_provider_and_model(model: str) -> Tuple[str, str]:
    """
    Get the provider and model from a string in the format "provider:model"
    If no provider is specified, it defaults to "openai".

    Args:
        model (str): The model string in the format "provider:model"

    Returns:
        tuple: A tuple with the provider and model
    """
    # If the OVERRIDE_WITH_OLLAMA_MODEL environment variable is set, use the Ollama model
    # in all cases. This is used in the preview mode or for tests.
    if config.OVERRIDE_WITH_OLLAMA_MODEL is not None:
        ollama_model = config.OVERRIDE_WITH_OLLAMA_MODEL
        return "ollama", ollama_model

    split_result = model.split(":")
    if len(split_result) == 1:
        # Assume default provider to be openai
        provider = "openai"
        model_name = split_result[0]
    elif len(split_result) > 2:
        # Some model names have :, so we need to join the rest of the string
        provider = split_result[0]
        model_name = ":".join(split_result[1:])
    else:
        provider = split_result[0]
        model_name = split_result[1]

    return provider, model_name


def get_async_client(
    provider: Literal[
        "openai",
        "mistral",
        "ollama",
        "solar",
        "together",
        "anyscale",
        "fireworks",
    ],
) -> AsyncOpenAI:
    if provider == "openai":
        return AsyncOpenAI()
    if provider == "mistral":
        return AsyncOpenAI(
            base_url="https://api.mistral.ai/v1/",
            api_key=os.getenv("MISTRAL_API_KEY"),
        )
    if provider == "ollama":
        return AsyncOpenAI(
            base_url="http://localhost:11434/v1/",
            api_key="ollama",
        )
    if provider == "solar":
        return AsyncOpenAI(
            base_url="https://api.upstage.ai/v1/solar/",
            api_key=os.getenv("SOLAR_API_KEY"),
        )
    if provider == "together":
        return AsyncOpenAI(
            base_url="https://api.together.xyz/v1/",
            api_key=os.getenv("TOGETHER_API_KEY"),
        )
    if provider == "anyscale":
        return AsyncOpenAI(
            base_url="https://api.endpoints.anyscale.com/v1/",
            api_key=os.getenv("ANYSCALE_API_KEY"),
        )
    if provider == "fireworks":
        return AsyncOpenAI(
            base_url="https://api.fireworks.ai/inference/v1/",
            api_key=os.getenv("FIREWORKS_API_KEY"),
        )
    raise NotImplementedError(f"Provider {provider} is not supported.")


def get_sync_client(
    provider: Literal[
        "openai",
        "mistral",
        "ollama",
        "solar",
        "together",
        "anyscale",
        "fireworks",
    ],
) -> OpenAI:
    if provider == "openai":
        return OpenAI()
    if provider == "mistral":
        return OpenAI(
            base_url="https://api.mistral.ai/v1/",
            api_key=os.getenv("MISTRAL_API_KEY"),
        )
    if provider == "ollama":
        return OpenAI(
            base_url="http://localhost:11434/v1/",
            api_key="ollama",
        )
    if provider == "solar":
        return OpenAI(
            base_url="https://api.upstage.ai/v1/solar/",
            api_key=os.getenv("SOLAR_API_KEY"),
        )
    if provider == "together":
        return OpenAI(
            base_url="https://api.together.xyz/v1/",
            api_key=os.getenv("TOGETHER_API_KEY"),
        )
    if provider == "anyscale":
        return OpenAI(
            base_url="https://api.endpoints.anyscale.com/v1/",
            api_key=os.getenv("ANYSCALE_API_KEY"),
        )
    if provider == "fireworks":
        return OpenAI(
            base_url="https://api.fireworks.ai/inference/v1/",
            api_key=os.getenv("FIREWORKS_API_KEY"),
        )
    raise NotImplementedError(f"Provider {provider} is not supported.")
