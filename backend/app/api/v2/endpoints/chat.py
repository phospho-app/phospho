from typing import Dict, Iterable, List, Literal, Optional, Union

import httpx
import openai
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from openai._types import NOT_GIVEN, Body, Headers, NotGiven, Query
from openai.types.chat import completion_create_params
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from openai.types.chat.chat_completion_stream_options_param import (
    ChatCompletionStreamOptionsParam,
)
from openai.types.chat.chat_completion_tool_choice_option_param import (
    ChatCompletionToolChoiceOptionParam,
)
from openai.types.chat.chat_completion_tool_param import ChatCompletionToolParam

from app.core import config
from app.security.authentification import authenticate_org_key
from app.services.mongo.predict import metered_prediction
from phospho.lab.language_models import get_async_client, get_provider_and_model

router = APIRouter(tags=["chat"])


@router.get(
    "/{project_id}/chat/completions",
    description="Create a chat completion",
)
async def create(
    self,
    *,
    project_id: str,
    messages: Iterable[ChatCompletionMessageParam],
    model: Literal["openai:gpt-4o",],
    frequency_penalty: Optional[float] | NotGiven = NOT_GIVEN,
    function_call: completion_create_params.FunctionCall | NotGiven = NOT_GIVEN,
    functions: Iterable[completion_create_params.Function] | NotGiven = NOT_GIVEN,
    logit_bias: Optional[Dict[str, int]] | NotGiven = NOT_GIVEN,
    logprobs: Optional[bool] | NotGiven = NOT_GIVEN,
    max_tokens: Optional[int] | NotGiven = NOT_GIVEN,
    n: Optional[int] | NotGiven = NOT_GIVEN,
    presence_penalty: Optional[float] | NotGiven = NOT_GIVEN,
    response_format: completion_create_params.ResponseFormat | NotGiven = NOT_GIVEN,
    seed: Optional[int] | NotGiven = NOT_GIVEN,
    stop: Union[Optional[str], List[str]] | NotGiven = NOT_GIVEN,
    stream: Optional[Literal[False]] | NotGiven = NOT_GIVEN,
    stream_options: Optional[ChatCompletionStreamOptionsParam] | NotGiven = NOT_GIVEN,
    temperature: Optional[float] | NotGiven = NOT_GIVEN,
    tool_choice: ChatCompletionToolChoiceOptionParam | NotGiven = NOT_GIVEN,
    tools: Iterable[ChatCompletionToolParam] | NotGiven = NOT_GIVEN,
    top_logprobs: Optional[int] | NotGiven = NOT_GIVEN,
    top_p: Optional[float] | NotGiven = NOT_GIVEN,
    user: str | NotGiven = NOT_GIVEN,
    extra_headers: Headers | None = None,
    extra_query: Query | None = None,
    extra_body: Body | None = None,
    timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    org: dict = Depends(authenticate_org_key),
    background_tasks: BackgroundTasks,
) -> ChatCompletion:
    """
    Generate a chat completion
    """
    # Get customer_id
    org_metadata = org["org"].get("metadata", {})
    org_id = org["org"]["org_id"]
    customer_id = None

    if "customer_id" in org_metadata.keys():
        customer_id = org_metadata.get("customer_id", None)

    if not customer_id and org_id != config.PHOSPHO_ORG_ID:
        raise HTTPException(
            status_code=402,
            detail="You need to add a payment method to access this service. Please update your payment details: https://platform.phospho.ai/org/settings/billing",
        )

    SUPPORTED_MODELS = ["openai:gpt-4o"]
    if model not in SUPPORTED_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Model {model} not supported or you don't have access to it.",
        )

    provider, model_name = get_provider_and_model(model)
    openai_client = get_async_client(provider)

    query_inputs = {
        "messages": messages,
        "model": model_name,
        "frequency_penalty": frequency_penalty,
        "function_call": function_call,
        "functions": functions,
        "logit_bias": logit_bias,
        "logprobs": logprobs,
        "max_tokens": max_tokens,
        "n": n,
        "presence_penalty": presence_penalty,
        "response_format": response_format,
        "seed": seed,
        "stop": stop,
        "stream": stream,
        "stream_options": stream_options,
        "temperature": temperature,
        "tool_choice": tool_choice,
        "tools": tools,
        "top_logprobs": top_logprobs,
        "top_p": top_p,
        "user": user,
        "extra_headers": extra_headers,
        "extra_query": extra_query,
        "extra_body": extra_body,
        "timeout": timeout,
    }
    response = await openai_client.chat.completions.create(
        **query_inputs,
    )
    if not response:
        raise HTTPException(
            status_code=500,
            detail="An error occurred while generating predictions.",
        )

    if org_id != config.PHOSPHO_ORG_ID:  # Only whitelisted org
        background_tasks.add_task(
            metered_prediction,
            org_id=org["org"]["org_id"],
            model_id=model,
            inputs=[query_inputs],
            predictions=[response],
            project_id=project_id,
        )

    return response
