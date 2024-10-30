"""
Collection of jobs for the laboratory.
Each job is a function that takes a message and a set of parameters and returns a result.
The result is a JobResult object.
"""

import logging
import math
import os
import random
import time
from collections import defaultdict
from typing import List, Literal, Optional, Tuple, cast

from phospho.models import (
    DetectionScope,
    JobResult,
    Message,
    ResultType,
    ScoreRange,
    ScoreRangeSettings,
    Task,
)
from phospho.utils import get_number_of_tokens, shorten_text

try:
    from openai import AsyncOpenAI, OpenAI
except ImportError:
    pass


from .language_models import get_async_client, get_provider_and_model, get_sync_client

logger = logging.getLogger(__name__)


def prompt_to_bool(
    message: Message,
    prompt: str,
    format_kwargs: Optional[dict] = None,
    model: str = "openai:gpt-4o",
) -> JobResult:
    """
    Runs a prompt on a message and returns a boolean result.
    """
    # Check if some Env variables override the default model and LLM provider
    provider, model_name = get_provider_and_model(model)
    openai_client = get_sync_client(provider)

    if format_kwargs is None:
        format_kwargs = {}

    formated_prompt = prompt.format(
        message_content=message.content,
        message_context=message.previous_messages_transcript(with_role=True),
        **format_kwargs,
    )
    response = openai_client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": formated_prompt,
            },
        ],
        max_tokens=1,
    )
    llm_response = response.choices[0].message.content

    # Cast the response to a bool
    if llm_response is None:
        bool_response = False
    else:
        bool_response = llm_response.lower() == "true"

    return JobResult(
        result_type=ResultType.bool,
        value=bool_response,
        logs=[formated_prompt, llm_response],
    )


def prompt_to_literal(
    message: Message,
    prompt: str,
    output_literal: List[str],
    format_kwargs: Optional[dict] = None,
    model: str = "openai:gpt-3.5-turbo",
) -> JobResult:
    """
    Runs a prompt on a message and returns a str from the list ouput_literal.
    """
    provider, model_name = get_provider_and_model(model)
    openai_client = get_sync_client(provider)

    if format_kwargs is None:
        format_kwargs = {}

    formated_prompt = prompt.format(
        message_content=message.transcript(with_role=True),
        message_context=message.transcript(
            only_previous_messages=True, with_previous_messages=True, with_role=True
        ),
        **format_kwargs,
    )
    response = openai_client.chat.completions.create(
        model=model_name,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": formated_prompt,
            },
        ],
        max_tokens=1,
        temperature=0,
    )

    response_content = response.choices[0].message.content
    literal_response = None
    if response_content is not None:
        response_content = response_content.strip()
        # Best scenario: Check if the response is in the output_literal
        if response_content in output_literal:
            return JobResult(
                result_type=ResultType.literal,
                value=response_content,
                logs=[formated_prompt, response.choices[0].message.content],
            )
        # Greedy: Check if the response contains one of the output_literal
        for literal in output_literal:
            if literal in response_content:
                return JobResult(
                    result_type=ResultType.literal,
                    value=response_content,
                    logs=[formated_prompt, response.choices[0].message.content],
                )

    return JobResult(
        result_type=ResultType.literal,
        value=literal_response,
        logs=[formated_prompt, response.choices[0].message.content],
    )


async def event_detection(
    message: Message,
    event_name: str,
    event_description: str,
    score_range_settings: Optional[ScoreRangeSettings] = None,
    detection_scope: DetectionScope = "task",
    model: str = "azure:gpt-4o",
    **kwargs,
) -> JobResult:
    """
    Detects if an event is present in a message.

    - We can use message metadatas to get examples of successful and unsuccessful interactions
    """
    # Identifier of the source of the evaluation, with the version of the model if phospho
    EVALUATION_SOURCE = "phospho-6"
    MAX_TOKENS = 128_000

    # Check if some Env variables override the default model and LLM provider
    provider, model_name = get_provider_and_model(model)
    async_openai_client = get_async_client(provider)

    if score_range_settings is None:
        score_range_settings = ScoreRangeSettings()
    if isinstance(score_range_settings, dict):
        score_range_settings = ScoreRangeSettings.model_validate(score_range_settings)
    if (
        score_range_settings.score_type == "category"
        and not score_range_settings.categories
    ):
        raise ValueError(
            f"Categories must be provided for category score type. Got: {score_range_settings.model_dump()}"
        )

    # We fetch examples for few shot
    successful_events = message.metadata.get("successful_events", [])
    unsuccessful_events = message.metadata.get("unsuccessful_events", [])

    assert isinstance(successful_events, list), "successful_events is not a list"
    assert isinstance(unsuccessful_events, list), "unsuccessful_events is not a list"

    successful_example = None
    for example in successful_events:
        if event_name == example["event_name"]:
            successful_example = example
            break

    unsuccessful_example = None
    for example in unsuccessful_events:
        if event_name == example["event_name"]:
            unsuccessful_example = example
            break

    # Build the prompt
    system_prompt = ""
    prompt = ""

    #
    if detection_scope == "system_prompt":
        system_prompt = (
            "You are an impartial judge reading an assistant system prompt. "
        )
        during_interaction = "in the system prompt"
        the_interaction = "system prompt"
    else:
        system_prompt = "You are an impartial judge reading a conversation between a user and an assistant. "
        during_interaction = "during the interaction"
        the_interaction = "interaction"

    if score_range_settings.score_type == "confidence":
        system_prompt += f"You must determine if the event '{event_name}' happened {during_interaction}."
    elif score_range_settings.score_type == "range":
        system_prompt = f"You must evaluate the event '{event_name}'."
    elif score_range_settings.score_type == "category":
        system_prompt = f"You must categorize the event '{event_name}'."

    if event_description is not None and len(event_description) > 0:
        system_prompt += f"""'{event_name}' is described to you like so:
'{event_description}'
"""
    else:
        system_prompt += f"""
You don't have a description for '{event_name}'. Base your evaluation on the context of the conversation and the name of the event.
"""

    if successful_example is not None:
        system_prompt += f"""
Here is an example of an interaction where the event '{event_name}' happened:
[EVENT DETECTED EXAMPLE START]
{successful_example['input']} -> {successful_example['output']}
[EVENT DETECTED EXAMPLE EXAMPLE END]
"""
    if unsuccessful_example is not None:
        system_prompt += f"""
Here is an example of an interaction where the event '{event_name}' did not happen:
[EVENT NOT DETECTED EXAMPLE START]
{unsuccessful_example['input']} -> {unsuccessful_example['output']}
[EVENT NOT DETECTED EXAMPLE END]
"""

    if detection_scope != "system_prompt":
        system_prompt += "\nI will now give you an interaction to evaluate."
    else:
        system_prompt += "\nI will now give you a system prompt to evaluate."

    if len(message.previous_messages) > 1 and "task" in detection_scope:
        truncated_context = shorten_text(
            message.latest_interaction_context(),
            MAX_TOKENS,
            get_number_of_tokens(prompt) + 100,
            how="right",
        )
        system_prompt += f"""
Here is the context of the conversation:
[CONTEXT START]
{truncated_context}
[CONTEXT END]
"""

    if detection_scope == "task":
        prompt += f"""Label the following interaction with the event '{event_name}':
[INTERACTION TO LABEL START]
{message.latest_interaction()}
[INTERACTION TO LABEL END]
"""
    elif detection_scope == "task_input_only":
        message_list = message.as_list()
        # Filter to keep only the user messages
        message_list = [m for m in message_list if m.role.lower() == "user"]
        if len(message_list) == 0:
            return JobResult(
                result_type=ResultType.bool,
                value=False,
                logs=["No user message in the interaction"],
            )
        truncated_context = shorten_text(
            message_list[-1].content,
            MAX_TOKENS,
            get_number_of_tokens(prompt) + 100,
            how="right",
        )

        prompt += f"""
Label the following user message with the event '{event_name}':
[INTERACTION TO LABEL START]
User: {truncated_context}
[INTERACTION TO LABEL END]
"""
    elif detection_scope == "task_output_only":
        message_list = message.as_list()
        # Filter to keep only the assistant messages
        message_list = [m for m in message_list if m.role.lower() == "assistant"]
        if len(message_list) == 0:
            return JobResult(
                result_type=ResultType.bool,
                value=False,
                logs=["No assistant message in the interaction"],
            )
        truncated_context = shorten_text(
            message_list[-1].content,
            MAX_TOKENS,
            get_number_of_tokens(prompt) + 100,
            how="right",
        )
        if len(message_list) == 0:
            return JobResult(
                result_type=ResultType.bool,
                value=False,
                logs=["No assistant message in the interaction"],
            )
        prompt += f"""
Label the following assistant message with the event '{event_name}':
[INTERACTION TO LABEL START]
Assistant: {truncated_context}
[INTERACTION TO LABEL END]
"""
    elif detection_scope == "session":
        truncated_context = shorten_text(
            message.transcript(with_role=True, with_previous_messages=True),
            MAX_TOKENS,
            get_number_of_tokens(prompt) + 100,
            how="right",
        )
        prompt += f"""
Label the following interaction with the event '{event_name}':
[INTERACTION TO LABEL START]
{truncated_context}
[INTERACTION TO LABEL END]
"""
    elif detection_scope == "system_prompt":
        # Detection on the system_prompt metadata in the message
        # The system_prompt is canonically stored in the task metadata
        message_task: Optional[Task] = message.metadata.get("task")
        if not isinstance(message_task, Task):
            return JobResult(
                result_type=ResultType.error,
                value=None,
                logs=["No task in the message"],
            )
        if not isinstance(message_task.metadata, dict):
            return JobResult(
                result_type=ResultType.error,
                value=None,
                logs=["No metadata in the task"],
            )
        system_prompt_in_message = message_task.metadata.get("system_prompt", None)
        if system_prompt_in_message is None:
            return JobResult(
                result_type=ResultType.error,
                value=None,
                logs=["No system_prompt in the task metadata"],
            )
        if not isinstance(system_prompt_in_message, str):
            return JobResult(
                result_type=ResultType.error,
                value=None,
                logs=["system_prompt in the message is not a string"],
            )
        truncated_context = shorten_text(
            system_prompt_in_message,
            MAX_TOKENS,
            get_number_of_tokens(prompt) + 100,
            how="right",
        )
        prompt += f"""
Label the following system prompt with the event '{event_name}':
[SYSTEM PROMPT TO LABEL START]
{truncated_context}
[SYSTEM PROMPT TO LABEL END]
"""
    else:
        raise ValueError(
            f"Unknown event_scope : {detection_scope}. Valid values are: {DetectionScope.__args__}"
        )

    if score_range_settings.score_type == "confidence":
        prompt += f"""
Did the event '{event_name}' happen {during_interaction}? 
Respond with only one word: Yes or No."""
    elif score_range_settings.score_type == "range":
        prompt += f"""
How would you assess the '{event_name}' {during_interaction}? 
Respond with a whole number between {score_range_settings.min} and {score_range_settings.max}.
"""
    elif (
        score_range_settings.score_type == "category"
        and score_range_settings.categories
    ):
        formatted_categories = "\n".join(
            [
                f"{i+1}. {category}"
                for i, category in enumerate(score_range_settings.categories)
            ]
        )
        prompt += f"""
How would you categorize the {the_interaction} according to the event '{event_name}'? 
Respond with a number between 1 and {len(score_range_settings.categories)}, where each number corresponds to a category:
{formatted_categories}
If the event '{event_name}' is not present in the {the_interaction} or you can't categorize it, respond with 0.
"""

    # Call the API
    start_time = time.time()
    try:
        if provider == "azure":
            # Azure does not support the logprobs parameter
            # Despite the docs saying it does: https://learn.microsoft.com/en-us/azure/ai-services/openai/reference#request-body-2
            # Issue: https://learn.microsoft.com/en-us/answers/questions/1692045/does-gpt-4-1106-preview-support-logprobs
            try:
                response = await async_openai_client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt,
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=5,
                    temperature=0,
                )
            except Exception as e:
                logger.warning(
                    f"event_detection call to Azure API failed: {e}. Falling back to OpenAI API."
                )
                async_openai_client = get_async_client("openai")
                # Fallback to OpenAI API
                response = await async_openai_client.chat.completions.create(
                    model=model_name,
                    messages=[
                        {
                            "role": "system",
                            "content": system_prompt,
                        },
                        {"role": "user", "content": prompt},
                    ],
                    max_tokens=5,
                    temperature=0,
                    logprobs=True,
                    top_logprobs=20,
                )
        else:
            response = await async_openai_client.chat.completions.create(
                model=model_name,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt,
                    },
                    {"role": "user", "content": prompt},
                ],
                max_tokens=5,
                temperature=0,
                logprobs=True,
                top_logprobs=20,
            )
    except Exception as e:
        logger.error(f"event_detection call to OpenAI API failed : {e}")
        return JobResult(
            result_type=ResultType.error,
            value=None,
            logs=[prompt, str(e)],
        )
    api_call_time = time.time() - start_time
    llm_response: Optional[str] = response.choices[0].message.content
    # Metadata
    llm_call = {
        "model": model_name,
        "prompt": prompt,
        "system_prompt": system_prompt,
        "llm_output": llm_response,
        "api_call_time": api_call_time,
    }
    metadata = {
        "api_call_time": api_call_time,
        "evaluation_source": EVALUATION_SOURCE,
        "llm_call": llm_call,
    }

    # If no response
    if response.choices is None or len(response.choices) == 0 or llm_response is None:
        return JobResult(result_type=ResultType.error, value=None, metadata=metadata)

    # If no logits, read the response
    if (
        response.choices[0].logprobs is None
        or response.choices[0].logprobs.content is None
    ):
        stripped_llm_response = llm_response.strip().lower()
        result_type = ResultType.error
        detected_event = None
        if score_range_settings.score_type == "confidence":
            if "yes" in stripped_llm_response:
                result_type = ResultType.bool
                detected_event = True
                metadata["score_range"] = ScoreRange(
                    score_type="confidence",
                    max=1,
                    min=0,
                    value=1,
                    options_confidence={"yes": 1},
                )
            elif "no" in stripped_llm_response:
                result_type = ResultType.bool
                detected_event = False
                metadata["score_range"] = ScoreRange(
                    score_type="confidence",
                    max=1,
                    min=0,
                    value=0,
                    options_confidence={"no": 1},
                )
            else:
                result_type = ResultType.error
                detected_event = None
        elif score_range_settings.score_type == "range":
            first_char = (
                stripped_llm_response[0] if len(stripped_llm_response) > 0 else ""
            )
            if first_char.isdigit():
                result_type = ResultType.bool
                detected_event = True
                score = float(first_char)
                metadata["score_range"] = ScoreRange(
                    score_type="range",
                    max=score_range_settings.max,
                    min=score_range_settings.min,
                    value=score,
                    options_confidence={str(score): 1},
                )
        elif (
            score_range_settings.score_type == "category"
            and score_range_settings.categories
        ):
            # Check if the response is a number or starts with a number
            first_char = (
                stripped_llm_response[0] if len(stripped_llm_response) > 0 else ""
            )
            if first_char.isdigit():
                llm_response_as_int = int(first_char)
                if llm_response_as_int >= 1 and llm_response_as_int <= len(
                    score_range_settings.categories
                ):
                    result_type = ResultType.literal
                    detected_event = True
                    score = llm_response_as_int
                    label = score_range_settings.categories[score - 1]
                    metadata["score_range"] = ScoreRange(
                        score_type="category",
                        value=score,
                        min=1,
                        max=len(score_range_settings.categories),
                        label=label,
                        options_confidence={label: 1},
                    )
                elif llm_response_as_int == 0:
                    result_type = ResultType.literal
                    detected_event = False
                    metadata["score_range"] = ScoreRange(
                        score_type="category",
                        value=0,
                        min=0,
                        max=len(score_range_settings.categories),
                        label="None",
                        options_confidence={"None": 1},
                    )
                else:
                    result_type = ResultType.error
                    detected_event = None
            else:
                # In this case, we check if the response is in the categories
                if stripped_llm_response in score_range_settings.categories:
                    result_type = ResultType.literal
                    detected_event = True
                    score = (
                        score_range_settings.categories.index(stripped_llm_response) + 1
                    )
                    metadata["score_range"] = ScoreRange(
                        score_type="category",
                        value=score,
                        min=1,
                        max=len(score_range_settings.categories),
                        label=stripped_llm_response,
                        options_confidence={stripped_llm_response: 1},
                    )
                elif stripped_llm_response == "none":
                    result_type = ResultType.literal
                    detected_event = False
                    metadata["score_range"] = ScoreRange(
                        score_type="category",
                        value=0,
                        min=0,
                        max=len(score_range_settings.categories),
                        label="None",
                        options_confidence={"None": 1},
                    )
                else:
                    result_type = ResultType.error
                    detected_event = None

        return JobResult(
            result_type=result_type, value=detected_event, metadata=metadata
        )

    # Interpret the logprobs to compute the Score
    first_logprobs = response.choices[0].logprobs.content[0].top_logprobs
    logprob_score: dict[str, float] = defaultdict(float)
    result_type = ResultType.bool
    # Parse the logprobs for relevant tokens
    if score_range_settings.score_type == "confidence":
        for logprob in first_logprobs:
            stripped_token = logprob.token.lower().strip()
            if stripped_token == "no":
                logprob_score["no"] += math.exp(logprob.logprob)
            if stripped_token == "yes":
                logprob_score["yes"] += math.exp(logprob.logprob)
    elif score_range_settings.score_type == "range":
        # Looking for tokens corresponding to the range (numbers)
        for logprob in first_logprobs:
            stripped_token = logprob.token.lower().strip()
            if stripped_token.isdigit():
                if (
                    int(stripped_token) >= score_range_settings.min
                    and int(stripped_token) <= score_range_settings.max
                ):
                    # Only keep the tokens in the range
                    # Note: Only works with 1-5 range!
                    logprob_score[stripped_token] += math.exp(logprob.logprob)
    elif (
        score_range_settings.score_type == "category"
        and score_range_settings.categories
    ):
        # Looking for tokens corresponding to the range of categories (numbers)
        for logprob in first_logprobs:
            stripped_token = logprob.token.lower().strip()
            if stripped_token.isdigit():
                token_as_int = int(stripped_token)
                if token_as_int >= 0 and token_as_int <= len(
                    score_range_settings.categories
                ):
                    # Only keep the tokens in the range
                    logprob_score[stripped_token] += math.exp(logprob.logprob)
    else:
        raise ValueError(f"Unknown score_type : {score_range_settings.score_type}.")
    # Normalize the scores so that they sum to 1
    total_score = sum(logprob_score.values())
    if total_score > 0:
        for key in logprob_score:
            logprob_score[key] /= total_score
    # Interpret the score and if the event is detected
    score = score_range_settings.min
    if score_range_settings.score_type == "confidence":
        # The response is the token with the highest logprob
        if logprob_score["yes"] > logprob_score["no"]:
            detected_event = True
            score = logprob_score["yes"]
        else:
            detected_event = False
            score = logprob_score["no"]
        label = "yes" if detected_event else "no"
        options_confidence = logprob_score
    elif score_range_settings.score_type == "range":
        # In range mode, the event is always marked as detected
        detected_event = True
        # The score is the weighted average of the token * logprob
        score = sum(
            float(key) * logprob_score[key] for key in logprob_score if key.isdigit()
        )
        label = str(int(score))
        options_confidence = logprob_score
    elif (
        score_range_settings.score_type == "category"
        and score_range_settings.categories
    ):
        # The score is the token with the highest logprob
        token_with_max_score = max(logprob_score, key=lambda x: logprob_score.get(x, 0))
        score = int(token_with_max_score)
        if score == 0:
            # No event detected
            detected_event = False
            label = "None"
        else:
            # Event detected
            detected_event = True
            label = score_range_settings.categories[score - 1]
        options_confidence = {
            score_range_settings.categories[int(token) - 1]: logprob
            for token, logprob in logprob_score.items()
            if token.isdigit()
            and int(token) <= len(score_range_settings.categories)
            and int(token) >= 0
        }

    metadata["logprob_score"] = logprob_score
    metadata["all_logprobs"] = [logprob.model_dump() for logprob in first_logprobs]
    metadata["score_range"] = ScoreRange(
        score_type=score_range_settings.score_type,
        max=score_range_settings.max,
        min=score_range_settings.min,
        value=score,
        label=label,
        options_confidence=options_confidence,
    )

    # Return the result
    return JobResult(result_type=result_type, value=detected_event, metadata=metadata)


async def evaluate_task(
    message: Message,
    model: str = "openai:gpt-4o",
    **kwargs,
) -> JobResult:
    """
    Evaluate a task:
    - We use llm as a judge with few shot examples and the possibility to provide a custom prompt to the evalutor

    Message.metadata = {
        "successful_examples": [{input, output, flag}],
        "unsuccessful_examples": [{input, output, flag}],
        "evaluation_prompt": str,
    }
    """
    from phospho.utils import fits_in_context_window

    # Check if some Env variables override the default model and LLM provider
    provider, model_name = get_provider_and_model(model)
    async_openai_client = get_async_client(provider)

    successful_evals = message.metadata.get("successful_evals", [])
    unsuccessful_evals = message.metadata.get("unsuccessful_evals", [])
    evaluation_prompt = message.metadata.get("evaluation_prompt", None)

    assert isinstance(successful_evals, list), "successful_evals is not a list"
    assert isinstance(unsuccessful_evals, list), "unsuccessful_evals is not a list"
    assert isinstance(evaluation_prompt, str) or evaluation_prompt is None

    # 128k is the max input length for gpt-4o, we remove 1k to be safe
    # TODO : Make this adaptative to model name
    max_tokens_input_lenght = 128 * 1000 - 1000

    merged_examples = successful_evals + unsuccessful_evals
    random.shuffle(merged_examples)

    # Additional metadata
    api_call_time: Optional[float] = None
    llm_call: Optional[dict] = None

    async def evaluation(
        system_prompt: str,
        prompt: str,
        model_name: str = "gpt-4o",
    ) -> Optional[Literal["success", "failure"]]:
        """
        Call the LLM API to get a classification of a task
        as a success or a failure.
        """
        nonlocal api_call_time
        nonlocal llm_call

        if not fits_in_context_window(prompt, max_tokens_input_lenght):
            logger.error("The prompt does not fit in the context window")
            # TODO : Fall back to a bigger model
            return None

        start_time = time.time()
        response = await async_openai_client.chat.completions.create(
            model=model_name,
            messages=[
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=5,  # We only need a small output
        )

        llm_response = response.choices[0].message.content
        api_call_time = time.time() - start_time

        llm_call = {
            "model": model_name,
            "system_prompt": system_prompt,
            "prompt": prompt,
            "llm_output": llm_response,
            "api_call_time": api_call_time,
            "evaluation_source": "phospho-6",
        }

        # Parse the llm response to avoid basic errors
        if llm_response is not None:
            llm_response = llm_response.strip()
            llm_response = llm_response.lower()
            if "success" in llm_response:
                llm_response = "success"
            if "failure" in llm_response:
                llm_response = "failure"

        if llm_response in ["success", "failure"]:
            return cast(Literal["success", "failure"], llm_response)
        else:
            # TODO : raise an error
            # llm_response = "undefined"
            logger.warning(
                f"LLM response not in ['success', 'failure']:\"{llm_response}\""
            )
            return None

    def build_prompt(
        message: Message,
        evaluation_prompt: Optional[str] = None,
        merged_examples: List[dict] = [],
    ) -> Tuple[str, str]:
        """
        Builds a prompt for the evaluation of a task,
        makes use of successful and unsuccessful examples as well as a custom evaluation prompt.

        We divide the prompt from the system prompt, this works much better than the previous prompt only approach.
        """
        prompt = """Here is the interaction between the assistant and the user that you have to evaluate:
[START INTERACTION]
"""

        if len(message.previous_messages) > 0:
            prompt += f"""{message.previous_messages_transcript(with_role=True)}"""

        prompt += f"""
{message.transcript(with_role=True)}
[END INTERACTION]

Respond with only one word: success or failure based on these guidelines:
"""
        system_prompt = """You are an impartial judge evaluating an interaction between a user and an assistant. You follow the given evaluation guidelines."""
        if evaluation_prompt:
            system_prompt += f"""
[EVALUATION GUIDELINES START]
{evaluation_prompt}
[EVALUATION GUIDELINES END]
"""
        else:
            system_prompt += """
[EVALUATION GUIDELINES START]
Give a positive answer if the assistant response was good, to the point, and relevant, give a negative answer if the assistant response was bad, inapropriate or irrelevent.
[EVALUATION GUIDELINES END]
"""
        if len(merged_examples) > 1:
            system_prompt += """Here are some examples of interactions:
[EXAMPLES START]"""
            for example in merged_examples:
                system_prompt += f"""
{example['input']} -> {example['output']} -> {example['flag']}"""

            system_prompt += """[EXAMPLES END]"""

        return system_prompt, prompt

    system_prompt, prompt = build_prompt(message, evaluation_prompt, merged_examples)
    flag = await evaluation(system_prompt, prompt, model_name=model_name)

    return JobResult(
        result_type=ResultType.literal,
        value=flag,
        logs=[prompt, flag],
        metadata={
            "api_call_time": api_call_time,
            "llm_call": llm_call,
        },
    )


def get_nb_tokens(
    message: Message, model: Optional[str] = "openai:gpt-4o", tokenizer=None
) -> JobResult:
    """
    Get the number of tokens in a message.
    """
    from phospho.lab.utils import num_tokens_from_messages

    if model is not None:
        provider, model = get_provider_and_model(model)

    return JobResult(
        result_type=ResultType.literal,
        value=num_tokens_from_messages([message.model_dump()], model, tokenizer),
    )


async def keyword_event_detection(
    message: Message,
    event_name: str,
    keywords: str,
    event_scope: DetectionScope = "task",
    **kwargs,
) -> JobResult:
    """
    Uses regexes to detect if an event is present in a message.
    """
    from re import search

    listExchangeToSearch: List[str] = []
    if event_scope == "task":
        listExchangeToSearch = [message.latest_interaction()]
    elif event_scope == "task_input_only":
        message_list = message.as_list()
        # Filter to keep only the user messages
        listExchangeToSearch = [
            " " + m.content + " " for m in message_list if m.role.lower() == "user"
        ]
    elif event_scope == "task_output_only":
        message_list = message.as_list()
        # Filter to keep only the assistant messages
        listExchangeToSearch = [
            " " + m.content + " " for m in message_list if m.role.lower() == "assistant"
        ]
    elif event_scope == "session":
        listExchangeToSearch = [
            message.transcript(with_role=True, with_previous_messages=True)
        ]
    elif event_scope == "system_prompt":
        message_task: Optional[Task] = message.metadata.get("task")
        if not isinstance(message_task, Task):
            return JobResult(
                result_type=ResultType.error,
                value=None,
                logs=["No task in the message"],
            )
        if not isinstance(message_task.metadata, dict):
            return JobResult(
                result_type=ResultType.error,
                value=None,
                logs=["No metadata in the task"],
            )
        system_prompt_in_message = message_task.metadata.get("system_prompt", None)
        if system_prompt_in_message is None:
            return JobResult(
                result_type=ResultType.error,
                value=None,
                logs=["No system_prompt in the task metadata"],
            )
        if not isinstance(system_prompt_in_message, str):
            return JobResult(
                result_type=ResultType.error,
                value=None,
                logs=["system_prompt in the message is not a string"],
            )
        listExchangeToSearch = [system_prompt_in_message]
    else:
        raise ValueError(
            f"Unknown event_scope : {event_scope}. Valid values are: {DetectionScope.__args__}"
        )

    # text to look into for the keywords
    text = " ".join(listExchangeToSearch).lower()

    # [ ,.:'/\n\r\t+=]{1} is used to match the keyword only if it is a separate word, because we don't want to match substrings
    keywordlist = [
        "[ ,.:'/\n\r\t+=]{1}"
        + keyword.strip().lower()  # we match the keyword in the middle of the text
        + "[ ,.:'/\n\r\t+=]{1}|^"
        + keyword.strip().lower()  # we match the keyword at the beginning of the text
        + "[ ,:'/.\n\r\t]{1}"
        + "|[ ,:'/.\n\r\t]{1}"
        + keyword.strip().lower()  # we match the keyword at the end of the text
        + "$"
        for keyword in keywords.split(",")
    ]

    # we use a regex pattern to match the keywords in the text
    regex_pattern = "|".join(keywordlist)

    try:
        result = search(regex_pattern, text)
        found = result is not None

        return JobResult(
            result_type=ResultType.bool,
            value=found,
            logs=[text, regex_pattern],
            metadata={
                "evaluation_source": "phospho-keywords",
                "score_range": ScoreRange(
                    score_type="confidence", max=1, min=0, value=1 if found else 0
                ),
            },
        )

    except Exception as e:
        return JobResult(
            result_type=ResultType.error,
            value=None,
            logs=[str(e)],
        )


async def regex_event_detection(
    message: Message,
    event_name: str,
    regex_pattern: str,
    event_scope: DetectionScope = "task",
    **kwargs,
) -> JobResult:
    """
    Uses regexes to detect if an event is present in a message.
    """
    from re import search

    listExchangeToSearch: List[str] = []
    if event_scope == "task":
        listExchangeToSearch = [message.latest_interaction()]

    elif event_scope == "task_input_only":
        message_list = message.as_list()
        # Filter to keep only the user messages
        listExchangeToSearch = [
            " " + m.content + " " for m in message_list if m.role.lower() == "user"
        ]
    elif event_scope == "task_output_only":
        message_list = message.as_list()
        # Filter to keep only the assistant messages
        listExchangeToSearch = [
            " " + m.content + " " for m in message_list if m.role.lower() == "assistant"
        ]
    elif event_scope == "session":
        listExchangeToSearch = [
            message.transcript(with_role=True, with_previous_messages=True)
        ]
    elif event_scope == "system_prompt":
        message_task: Optional[Task] = message.metadata.get("task")
        if not isinstance(message_task, Task):
            return JobResult(
                result_type=ResultType.error,
                value=None,
                logs=["No task in the message"],
            )
        if not isinstance(message_task.metadata, dict):
            return JobResult(
                result_type=ResultType.error,
                value=None,
                logs=["No metadata in the task"],
            )
        system_prompt_in_message = message_task.metadata.get("system_prompt", None)
        if system_prompt_in_message is None:
            return JobResult(
                result_type=ResultType.error,
                value=None,
                logs=["No system_prompt in the task metadata"],
            )
        if not isinstance(system_prompt_in_message, str):
            return JobResult(
                result_type=ResultType.error,
                value=None,
                logs=["system_prompt in the message is not a string"],
            )
        listExchangeToSearch = [system_prompt_in_message]
    else:
        raise ValueError(
            f"Unknown event_scope : {event_scope}. Valid values are: {DetectionScope.__args__}"
        )

    text = " ".join(listExchangeToSearch)

    try:
        result = search(regex_pattern, text)
        found = result is not None

        return JobResult(
            result_type=ResultType.bool,
            value=found,
            logs=[text, regex_pattern],
            metadata={
                "evaluation_source": "phospho-regex",
                "score_range": ScoreRange(
                    score_type="confidence", max=1, min=0, value=1 if found else 0
                ),
            },
        )

    except Exception as e:
        return JobResult(
            result_type=ResultType.error,
            value=None,
            logs=[str(e)],
        )
