from typing import Any, Dict, Iterable, List, Literal, Optional, Union

from app.db.mongo import get_mongo_db
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from loguru import logger
from openai.types.chat.chat_completion import ChatCompletion


from app.core import config
from app.security.authentification import authenticate_org_key
from app.services.mongo.predict import metered_prediction
from phospho.lab.language_models import get_async_client, get_provider_and_model
import pydantic

from app.services.mongo.projects import get_project_by_id
from app.services.mongo.organizations import create_project_by_org
from app.services.mongo.extractor import ExtractorClient
from app.api.v2.models.log import LogEvent

router = APIRouter(tags=["chat"])


class ChatCompletionMessageParam(pydantic.BaseModel):
    content: str
    role: Literal["system", "user", "assistant", "tool", "function"]
    name: str | None = None
    function_call: Any | None = None  # will be ignored
    tool_calls: Iterable[Any] | None = None  # will be ignored
    tool_call_id: str | None = None  # will be ignored


class CreateRequest(pydantic.BaseModel):
    messages: List[ChatCompletionMessageParam]
    model: Literal["openai:gpt-4o", "openai:gpt-4o-mini"]
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
    # stream: Optional[Literal[False]] | None = None
    # stream_options: Optional[ChatCompletionStreamOptionsParam] | None = None
    temperature: Optional[float] | None = None
    # tool_choice: ChatCompletionToolChoiceOptionParam | None = None
    # tools: Iterable[ChatCompletionToolParam] | None = None
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
):
    mongo_db = await get_mongo_db()
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
    input = None
    if create_request.messages:
        input = create_request.messages[-1].content
    system_prompt = None
    if create_request.messages:
        # Look for the system_prompt in the messages
        system_prompt_list = [m for m in create_request.messages if m.role == "system"]
        if system_prompt_list:
            system_prompt = system_prompt_list[0].content

    output = response.choices[0].message.content

    if input:
        await extractor_client.run_process_log_for_tasks(
            logs_to_process=[
                LogEvent(
                    project_id=logging_project_id,
                    input=input,
                    output=output,
                    metadata={
                        "model": create_request.model,
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


@router.post(
    "/{project_id}/chat/completions",
    description="Create a chat completion",
)
async def create(
    project_id: str,
    create_request: CreateRequest,
    background_tasks: BackgroundTasks,
    org: dict = Depends(authenticate_org_key),
) -> ChatCompletion:
    """
    Generate a chat completion

    The org identified by the API key must have access to the completion service.
    This means that the metadata has_completion_access must be set to True in Propelauth.
    """
    # Get customer_id
    logger.debug(f"Creating chat completion: {create_request}")
    org_metadata = org["org"].get("metadata", {})
    org_id = org["org"]["org_id"]
    customer_id = None

    if "customer_id" in org_metadata.keys():
        customer_id = org_metadata.get("customer_id", None)

    if (
        not customer_id
        and org_id != config.PHOSPHO_ORG_ID
        and config.ENVIRONMENT != "preview"
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
    if not org_metadata.get("has_completion_access", False):
        logger.warning(
            f"Org {org_id} does not have access to the completion service. Skipping metered prediction."
        )
        raise HTTPException(
            status_code=402,
            detail="You need to request access to this feature to the phospho team. Please contact us at contact@phospho.ai",
        )

    SUPPORTED_MODELS = [
        "openai:gpt-4o"
    ]  # Add "openai:gpt-4o-mini" and update the pricing accordingly
    if create_request.model not in SUPPORTED_MODELS:
        raise HTTPException(
            status_code=400,
            detail=f"Model {create_request.model} not supported or you don't have access to it.",
        )

    provider, model_name = get_provider_and_model(create_request.model)

    if (
        org_id != "818886b3-0ff7-4528-8bb9-845d5ecaa80d"
    ):  # TODO: This is an exception for a custom org, temporary
        # For this endpoint, we route requests to Azure OpenAI
        provider = "azure"
    openai_client = get_async_client(provider)

    # Change the model name to the one used by OpenAI
    create_request.model = model_name

    query_inputs = create_request.model_dump()
    response = await openai_client.chat.completions.create(
        **query_inputs,
    )
    if not response:
        raise HTTPException(
            status_code=500,
            detail="An error occurred while generating predictions.",
        )

    if org_id != config.PHOSPHO_ORG_ID and config.ENVIRONMENT == "production":
        background_tasks.add_task(
            metered_prediction,
            org_id=org["org"]["org_id"],
            model_id=f"{provider}:{model_name}",
            inputs=[create_request.model_dump()],
            predictions=[response.model_dump()],
            project_id=project_id,
        )
        background_tasks.add_task(
            log_to_project,
            org_id=org["org"]["org_id"],
            project_id=project_id,
            create_request=create_request,
            response=response,
        )

    return response
