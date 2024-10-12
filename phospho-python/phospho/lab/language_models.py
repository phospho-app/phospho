import os
from typing import Literal, Optional, Tuple

import phospho.config as config

try:
    from openai import AsyncOpenAI, OpenAI, AsyncAzureOpenAI, AzureOpenAI

except ImportError:
    # Define dummy classes to avoid import errors
    class AsyncOpenAI:
        pass

    class OpenAI:
        pass

    class AsyncAzureOpenAI:
        pass

    class AzureOpenAI:
        pass


def get_provider_and_model(
    model: str,
) -> Tuple[str, str]:
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
        "azure",
        # phospho means the Tak Search service for now (in private monorepo)
        "phospho",
    ],
    api_key: Optional[str] = None,
) -> AsyncOpenAI:
    """
    Return an async OpenAI client for the specified provider.
    """
    try:
        from openai import AsyncOpenAI, AsyncAzureOpenAI
    except ImportError:
        raise ImportError(
            "OpenAI is not installed. Please install it using `pip install openai`"
        )

    if provider == "openai":
        return AsyncOpenAI()
    if provider == "mistral":
        return AsyncOpenAI(
            base_url="https://api.mistral.ai/v1/",
            api_key=api_key or os.getenv("MISTRAL_API_KEY"),
        )
    if provider == "ollama":
        return AsyncOpenAI(
            base_url="http://localhost:11434/v1/",
            api_key="ollama",
        )
    if provider == "solar":
        return AsyncOpenAI(
            base_url="https://api.upstage.ai/v1/solar/",
            api_key=api_key or os.getenv("SOLAR_API_KEY"),
        )
    if provider == "together":
        return AsyncOpenAI(
            base_url="https://api.together.xyz/v1/",
            api_key=api_key or os.getenv("TOGETHER_API_KEY"),
        )
    if provider == "anyscale":
        return AsyncOpenAI(
            base_url="https://api.endpoints.anyscale.com/v1/",
            api_key=api_key or os.getenv("ANYSCALE_API_KEY"),
        )
    if provider == "fireworks":
        return AsyncOpenAI(
            base_url="https://api.fireworks.ai/inference/v1/",
            api_key=api_key or os.getenv("FIREWORKS_API_KEY"),
        )
    if provider == "azure":
        if os.getenv("AZURE_OPENAI_KEY") is None:
            raise ValueError("AZURE_OPENAI_KEY environment variable is not set.")
        if os.getenv("AZURE_OPENAI_ENDPOINT") is None:
            raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is not set.")

        return AsyncAzureOpenAI(
            # https://learn.microsoft.com/azure/ai-services/openai/reference#rest-api-versioning
            api_version="2023-03-15-preview",
            # https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource?pivots=web-portal#create-a-resource
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            api_key=os.environ.get("AZURE_OPENAI_KEY"),
        )
    if provider == "phospho":
        if os.getenv("TAK_SEARCH_URL") is None:
            raise ValueError("TAK_SEARCH_URL environment variable is not set.")
        if os.getenv("TAK_APP_API_KEY") is None:
            raise ValueError("TAK_APP_API_KEY environment variable is not set.")
        return AsyncOpenAI(
            base_url=f"{os.getenv('TAK_SEARCH_URL')}/v1/",
            api_key=os.getenv("TAK_APP_API_KEY"),
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
    api_key: Optional[str] = None,
) -> OpenAI:
    """
    Return a sync OpenAI client for the specified provider.
    """
    try:
        from openai import OpenAI
    except ImportError:
        raise ImportError(
            "OpenAI is not installed. Please install it using `pip install openai`"
        )

    if provider == "openai":
        return OpenAI()
    if provider == "mistral":
        return OpenAI(
            base_url="https://api.mistral.ai/v1/",
            api_key=api_key or os.getenv("MISTRAL_API_KEY"),
        )
    if provider == "ollama":
        return OpenAI(
            base_url="http://localhost:11434/v1/",
            api_key="ollama",
        )
    if provider == "solar":
        return OpenAI(
            base_url="https://api.upstage.ai/v1/solar/",
            api_key=api_key or os.getenv("SOLAR_API_KEY"),
        )
    if provider == "together":
        return OpenAI(
            base_url="https://api.together.xyz/v1/",
            api_key=api_key or os.getenv("TOGETHER_API_KEY"),
        )
    if provider == "anyscale":
        return OpenAI(
            base_url="https://api.endpoints.anyscale.com/v1/",
            api_key=api_key or os.getenv("ANYSCALE_API_KEY"),
        )
    if provider == "fireworks":
        return OpenAI(
            base_url="https://api.fireworks.ai/inference/v1/",
            api_key=api_key or os.getenv("FIREWORKS_API_KEY"),
        )
    if provider == "azure":
        if os.getenv("AZURE_OPENAI_KEY") is None:
            raise ValueError("AZURE_OPENAI_KEY environment variable is not set.")
        if os.getenv("AZURE_OPENAI_ENDPOINT") is None:
            raise ValueError("AZURE_OPENAI_ENDPOINT environment variable is not set.")

        return AzureOpenAI(
            # https://learn.microsoft.com/azure/ai-services/openai/reference#rest-api-versioning
            api_version="2023-03-15-preview",
            # https://learn.microsoft.com/azure/cognitive-services/openai/how-to/create-resource?pivots=web-portal#create-a-resource
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT", ""),
            api_key=os.environ.get("AZURE_OPENAI_KEY"),
        )

    raise NotImplementedError(f"Provider {provider} is not supported.")
