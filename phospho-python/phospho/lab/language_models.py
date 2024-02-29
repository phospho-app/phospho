from abc import ABC, abstractmethod
from phospho import config

import openai
import ollama
import mistralai
from mistralai.client import MistralClient


class BaseLanguageModel(ABC):
    @abstractmethod
    def invoke(self, *args, **kwargs) -> str:
        pass


class OpenAIModel(BaseLanguageModel):
    """
    A class to interact with the OpenAI API.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str,
        temperature: float = 0.0,
        max_tokens: int = 1,
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Create the async client
        self._client = openai.Client(api_key=api_key)

    def invoke(self, prompt) -> str:
        response = self._client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=self.max_tokens,
            temperature=self.temperature,
        )
        return response.choices[0].message.content


class AsyncOpenAIModel(BaseLanguageModel):
    """
    A class to interact with the OpenAI API.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str,
        temperature: float = 0.0,
        max_tokens: int = 1,
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Create the async client
        self._async_client = openai.AsyncClient(api_key=api_key)

    async def invoke(self, prompt) -> str:
        response = await self._async_client.chat.completions.create(
            model=self.model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1,
            temperature=0,
        )
        return response.choices[0].message.content


class OllamaModel(BaseLanguageModel):
    """
    A class to interact with the Ollama API of a model running locally.
    We have it return only one token.
    """

    def __init__(
        self,
        model_name: str,
    ):
        self.model_name = model_name

    def invoke(self, prompt) -> str:
        stream = ollama.chat(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
        )

        for chunk in stream:
            return chunk["message"]["content"]


class MistralModel(BaseLanguageModel):
    """
    A class to interact with the Mistral API.
    """

    def __init__(
        self,
        api_key: str,
        model_name: str,
        temperature: float = 0.0,
        max_tokens: int = 1,
    ):
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens

        # Create the async client
        self._client = MistralClient(api_key=api_key)

    def invoke(self, prompt) -> str:
        messages = [
            mistralai.models.chat_completion.ChatMessage(role="user", content=prompt)
        ]

        # No streaming
        chat_response = self._client.chat(
            model=self.model_name,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        return chat_response.choices[0].message.content


def language_model_from_id(model_id: str) -> BaseLanguageModel or None:
    """
    Mapping of model id to language model object.
    Return a language model object from an ID.
    """
    # OpenAI API
    if model_id == "openai:gpt-3.5-turbo":
        return OpenAIModel(
            api_key=config.OPENAI_API_KEY,
            model_name="gpt-3.5-turbo",
        )
    if model_id == "openai:gpt-4":
        return OpenAIModel(
            api_key=config.OPENAI_API_KEY,
            model_name="gpt-4",
        )
    # Ollama local API
    if model_id == "ollama:mistral-7B":
        return OllamaModel(
            model_name="mistral",
        )
    # Mistral AI API
    if model_id == "mistral:open-mistral-7b":
        return MistralModel(
            api_key=config.MISTRAL_API_KEY,
            model_name="open-mistral-7b",
        )
    if model_id == "mistral:open-mixtral-8x7b":
        return MistralModel(
            api_key=config.MISTRAL_API_KEY,
            model_name="open-mixtral-8x7b",
        )
    if model_id == "mistral:mistral-small-latest":
        return MistralModel(
            api_key=config.MISTRAL_API_KEY,
            model_name="mistral-small-latest",
        )
    if model_id == "mistral:mistral-medium-latest":
        return MistralModel(
            api_key=config.MISTRAL_API_KEY,
            model_name="mistral-medium-latest",
        )
    if model_id == "mistral:mistral-large-latest":
        return MistralModel(
            api_key=config.MISTRAL_API_KEY,
            model_name="mistral-large-latest",
        )

    return None
