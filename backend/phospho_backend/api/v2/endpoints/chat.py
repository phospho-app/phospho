from typing import (
    Any,
    Dict,
    Iterable,
    List,
    Literal,
    Optional,
    Union,
    AsyncIterator,
    Tuple,
)
import json
from fastapi.requests import Request
from fastapi.responses import StreamingResponse
from fastapi_simple_rate_limiter import rate_limiter  # type: ignore
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from loguru import logger
from openai.types.chat.chat_completion import (
    ChatCompletion,
    ChatCompletionMessage,
    Choice,
)
from openai.types.chat.chat_completion_chunk import ChatCompletionChunk
from openai import AsyncOpenAI

from phospho_backend.core import config
from phospho_backend.security.authentification import authenticate_org_key
from phospho_backend.services.mongo.predict import metered_prediction
from phospho.lab.language_models import get_async_client, get_provider_and_model
import pydantic

from phospho_backend.services.mongo.projects import get_project_by_id
from phospho_backend.services.mongo.organizations import create_project_by_org
from phospho_backend.services.mongo.extractor import ExtractorClient
from phospho_backend.api.v2.models.log import LogEvent
from typing import cast
from propelauth_py.types.user import OrgApiKeyValidation  # type: ignore


router = APIRouter(tags=["chat"])


class FunctionCallModel(pydantic.BaseModel):
    arguments: str
    name: str


class FunctionModel(pydantic.BaseModel):
    arguments: str
    name: str


class ChatCompletionMessageToolCallModel(pydantic.BaseModel):
    id: str
    function: FunctionModel
    type: Literal["function"]


class ChatCompletionMessageParamModel(pydantic.BaseModel):
    content: str
    role: Literal["system", "user", "assistant", "tool", "function"]
    name: str | None = None
    function_call: FunctionCallModel | None = None  # deprecated
    tool_calls: Iterable[ChatCompletionMessageToolCallModel] | None = None
    tool_call_id: str | None = None


class FunctionDefinitionModel(pydantic.BaseModel):
    name: str
    description: str
    parameters: dict
    strict: Optional[bool] = False


class ChatCompletionToolParamModel(pydantic.BaseModel):
    function: FunctionDefinitionModel
    type: Literal["function"] = "function"


class CreateRequest(pydantic.BaseModel):
    messages: List[ChatCompletionMessageParamModel]
    model: Literal[
        "openai:gpt-4o",
        "openai:gpt-4o-mini",
        "mistral:mistral-large-latest",
        "mistral:mistral-small-latest",
        # Pointers for the tak service in API
        "phospho:tak-large",
    ]
    frequency_penalty: Optional[float] | None = None
    # function_call: completion_create_params.FunctionCall | None = None
    # functions: Iterable[completion_create_params.Function] | None = None
    logit_bias: Optional[Dict[str, int]] | None = None
    logprobs: Optional[bool] | None = None
    max_tokens: Optional[int] | None = None
    n: Optional[int] | None = None
    presence_penalty: Optional[float] | None = None
    # response_format: completion_create_params.ResponseFormat | None = None
    seed: Optional[int] | None = None
    stop: Union[Optional[str], List[str]] | None = None
    stream: Optional[bool] | None = None
    # stream_options: Optional[ChatCompletionStreamOptionsParam] | None = None
    temperature: Optional[float] | None = None
    tool_choice: (
        Union[Literal["none", "auto", "required"], ChatCompletionToolParamModel] | None
    ) = None
    tools: Iterable[ChatCompletionToolParamModel] | None = None
    top_logprobs: Optional[int] | None = None
    top_p: Optional[float] | None = None
    user: str | None = None
    # extra_headers: Headers | None = None
    # extra_query: Query | None = None
    # extra_body: Body | None = None
    timeout: float | None | None = None


async def log_to_project(
    org_id: str,
    project_id: str,
    create_request: CreateRequest,
    response: ChatCompletion,
    model_name: Literal[
        "gpt-4o",
        "gpt-4o-mini",
        "mistral-large-latest",
        "mistral-small-latest",
        "tak-large",
    ],
):
    logging_project_id = project_id
    logger.info(f"Logging completion to project {logging_project_id}")

    try:
        logging_project = await get_project_by_id(logging_project_id)
    except Exception as e:
        logger.warning(f"Error getting project {logging_project_id}: {e}")
        logging_project = None

    if logging_project is None:  # No logging project setup
        # Create a new project
        logging_project = await create_project_by_org(
            org_id=org_id, user_id=None, project_name="Completions"
        )
        logger.info(f"Creating logging project for org {org_id}: {logging_project}")
        logging_project_id = logging_project.id

    # Log the completion to the project
    extractor_client = ExtractorClient(
        org_id=org_id,
        project_id=logging_project_id,
    )

    input = create_request.messages[-1].content if create_request.messages else None
    system_prompt = next(
        (m.content for m in create_request.messages if m.role == "system"), None
    )

    if input is None and system_prompt:
        input = system_prompt

    output = response.choices[0].message.content

    if input:
        await extractor_client.run_process_log_for_tasks(
            logs_to_process=[
                LogEvent(
                    project_id=logging_project_id,
                    input=input,
                    output=output,
                    metadata={
                        "model": model_name,
                        "frequency_penalty": create_request.frequency_penalty,
                        "max_tokens": create_request.max_tokens,
                        "seed": create_request.seed,
                        "temperature": create_request.temperature,
                        "system_prompt": system_prompt,
                    },
                )
            ]
        )
    else:
        logger.warning("No input found for logging completion.")


async def stream_and_capture(
    openai_client: AsyncOpenAI, query_inputs: Dict[str, Any]
) -> AsyncIterator[Tuple[Union[ChatCompletionChunk, ChatCompletion], ChatCompletion]]:
    full_response = ChatCompletion(
        id="", choices=[], created=0, model="", object="chat.completion", usage=None
    )
    try:
        async for chunk in await openai_client.chat.completions.create(**query_inputs):
            if isinstance(chunk, ChatCompletionChunk):
                if full_response.id == "":
                    full_response.id = chunk.id
                    full_response.created = chunk.created
                    full_response.model = chunk.model

                for choice in chunk.choices:
                    if len(full_response.choices) <= choice.index:
                        full_response.choices.append(
                            Choice(
                                index=choice.index,
                                message=ChatCompletionMessage(
                                    role="assistant", content=""
                                ),
                                finish_reason="stop",  # Initialize with a valid value
                            )
                        )

                    current_choice = full_response.choices[choice.index]

                    if (
                        choice.delta.content is not None
                        and current_choice.message.content is not None
                    ):
                        current_choice.message.content += choice.delta.content

                    if choice.finish_reason is not None:
                        current_choice.finish_reason = choice.finish_reason

            yield chunk, full_response
    except Exception as e:
        logger.error(f"Error in stream_and_capture: {e}")
        raise


async def log_and_meter(
    org_id: str,
    project_id: str,
    create_request: CreateRequest,
    response: ChatCompletion,
    provider: str,
    model_name: Literal[
        "gpt-4o",
        "gpt-4o-mini",
        "mistral-large-latest",
        "mistral-small-latest",
        "tak-large",
    ],
) -> None:
    logger.debug(f"Response: {response.model_dump(exclude_none=True)}")
    if org_id != config.PHOSPHO_ORG_ID and config.ENVIRONMENT == "production":
        await metered_prediction(
            org_id=org_id,
            model_id=f"{provider}:{model_name}",
            inputs=[create_request.model_dump(exclude_none=True)],
            predictions=[response.model_dump(exclude_none=True)],
            project_id=project_id,
        )
    await log_to_project(
        org_id=org_id,
        project_id=project_id,
        create_request=create_request,
        response=response,
        model_name=model_name,
    )


@router.post(
    "/{project_id}/chat/completions",
    description="Create a chat completion",
)
@router.post(
    "/{project_id}/v1/chat/completions",
    description="Create a chat completion",
)
@rate_limiter(limit=500, seconds=60)
async def create(
    project_id: str,
    request: Request,
    create_request: CreateRequest,
    background_tasks: BackgroundTasks,
    org: OrgApiKeyValidation = Depends(authenticate_org_key),
):  # Can be ChatCompletion or StreamingResponse
    """
    Generate a chat completion

    The org identified by the API key must have access to the completion service.
    This means that the metadata has_completion_access must be set to True in Propelauth.
    """
    # Get customer_id
    logger.info(f"Received chat completions request for project {project_id}")
    org_metadata = org.org.metadata or {}
    org_id = org.org.org_id
    customer_id = None

    if "customer_id" in org_metadata.keys():
        customer_id = org_metadata.get("customer_id", None)

    if (
        not customer_id
        and org_id not in [config.PHOSPHO_ORG_ID, config.TEST_PROPELAUTH_ORG_ID]
        and (config.ENVIRONMENT == "production" or config.ENVIRONMENT == "staging")
    ):
        if config.ENVIRONMENT != "test":
            raise HTTPException(
                status_code=402,
                detail="You need to add a payment method to access this service. Please update your payment details: https://platform.phospho.ai/org/settings/billing",
            )
        logger.warning(
            f"Customer ID not found for org_id: {org_id}. Skipping metered prediction. Will trigger a 402 error in production."
        )

    # Check that the org has access to the completion service
    if (
        not org_metadata.get("has_completion_access", False)
        and config.ENVIRONMENT == "production"
    ):
        logger.warning(
            f"Org {org_id} does not have access to the completion service. Skipping metered prediction."
        )
        raise HTTPException(
            status_code=402,
            detail="You need to request access to this feature to the phospho team. Please contact us at contact@phospho.ai",
        )

    # Now, the customer has access to the completion service

    SUPPORTED_MODELS = [
        "openai:gpt-4o",
        "openai:gpt-4o-mini",
        "mistral:mistral-large-latest",
        "mistral:mistral-small-latest",
        "phospho:tak-large",
    ]
    if create_request.model not in SUPPORTED_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Model {create_request.model} not supported or you don't have access to it.",
        )

    provider, model_name = get_provider_and_model(create_request.model)

    model_name = cast(
        Literal[
            "gpt-4o",
            "gpt-4o-mini",
            "mistral-large-latest",
            "mistral-small-latest",
            "tak-large",
        ],
        model_name,
    )

    # Redirect openai to Azure
    if (
        provider == "openai" and org_id != "818886b3-0ff7-4528-8bb9-845d5ecaa80d"
    ):  # We don't route Y to Azure
        provider = "azure"

    client = get_async_client(
        cast(
            Literal["openai", "azure", "mistral", "phospho"],
            provider,
        )
    )

    query_inputs = create_request.model_dump(exclude_none=True)
    # Update the model from provider:model_name to model_name (ex: openai:gpt-4o to gpt-4o)
    query_inputs["model"] = model_name

    should_stream = query_inputs.get("stream", False)

    if should_stream:

        async def generate() -> AsyncIterator[str]:
            try:
                async for chunk, full_response in stream_and_capture(
                    client, query_inputs
                ):
                    yield f"data: {chunk.model_dump_json()}\n\n"

                yield "data: [DONE]\n\n"

                # Perform logging and metering tasks with the aggregated full_response
                background_tasks.add_task(
                    log_and_meter,
                    org_id=org["org"]["org_id"],
                    project_id=project_id,
                    create_request=create_request,
                    response=full_response,
                    provider=provider,
                    model_name=model_name,
                )
            except Exception as e:
                logger.error(f"Error in generate: {e}")
                error_json = {"error": {"message": str(e), "type": type(e).__name__}}
                yield f"data: {json.dumps(error_json)}\n\n"
                yield "data: [DONE]\n\n"
                raise

        return StreamingResponse(generate(), media_type="text/event-stream")
    else:
        # Non-streaming response
        try:
            response: ChatCompletion = await client.chat.completions.create(
                **query_inputs
            )
            # Perform logging and metering tasks
            background_tasks.add_task(
                log_and_meter,
                org_id=org["org"]["org_id"],
                project_id=project_id,
                create_request=create_request,
                response=response,
                provider=provider,
                model_name=model_name,
            )

            return response
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
