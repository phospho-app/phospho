"""
Collection of jobs for the laboratory.
Each job is a function that takes a message and a set of parameters and returns a result.
The result is a JobResult object.
"""

import logging
import os
import random
import time
from typing import List, Literal, Optional, cast

try:
    from openai import AsyncOpenAI, OpenAI
except ImportError:
    pass

from phospho import config

from .language_models import get_async_client, get_provider_and_model, get_sync_client
from .models import JobResult, Message, ResultType

logger = logging.getLogger(__name__)


def prompt_to_bool(
    message: Message,
    prompt: str,
    format_kwargs: Optional[dict] = None,
    model: str = "openai:gpt-3.5-turbo",
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
    model: str = "openai:gpt-3.5-turbo",
) -> JobResult:
    """
    Detects if an event is present in a message.
    """

    # Check if some Env variables override the default model and LLM provider
    provider, model_name = get_provider_and_model(model)
    async_openai_client = get_async_client(provider)

    # Build the prompt
    if len(message.previous_messages) > 0:
        prompt = f"""
You are classifying an interaction between an end user and an assistant. The assistant is a chatbot that can perform tasks for the end user and answer his questions. 
The assistant might make some mistakes or not be useful.
The event you are looking for is: {event_description}
The name of the event is: {event_name}

Here is the transcript of the interaction:
[START INTERACTION]
{message.latest_interaction()}
[END INTERACTION]

You have to say if the event is present in the transcript or not. Respond with only one word, True or False.
    """
    else:
        prompt = f"""
You are classifying an interaction between an end user and an assistant. The assistant is a chatbot that can perform tasks for the end user and answer his questions. 
The assistant might make some mistakes or not be useful.
The event you are looking for is: {event_description} 
The name of the event is: {event_name}

Here are the previous messages of the conversation before the interaction to help you better understand the extract:
[START CONTEXT]
{message.latest_interaction_context()}
[END CONTEXT]

Here is the transcript of the interaction:
[START INTERACTION]
{message.latest_interaction()}
[END INTERACTION]

You have to say if the event is present in the transcript or not. Respond with only one word, True or False.
    """

    logger.debug(f"event_detection prompt : {prompt}")

    # Call the API
    start_time = time.time()

    try:
        response = await async_openai_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1,
            temperature=0,
        )
    except Exception as e:
        logger.error(f"event_detection call to OpenAI API failed : {e}")
        return JobResult(
            result_type=ResultType.error,
            value=None,
            logs=[prompt, str(e)],
        )

    api_call_time = time.time() - start_time

    logger.debug(f"event_detection call to OpenAI API ({api_call_time} sec)")

    # Parse the response
    llm_response = response.choices[0].message.content
    logger.debug(f"event_detection llm_response : {llm_response}")
    if llm_response is not None:
        llm_response = llm_response.strip()

    # Validate the output
    result_type = ResultType.error
    detected_event = None
    if llm_response is not None:
        llm_response = llm_response[:4].lower()
        if llm_response == "true":
            result_type = ResultType.bool
            detected_event = True
        elif llm_response == "fals":
            result_type = ResultType.bool
            detected_event = False

    # Identifier of the source of the evaluation, with the version of the model if phospho
    evaluation_source = "phospho-4"

    logger.debug(f"event_detection detected event {event_name} : {detected_event}")
    # Return the result
    return JobResult(
        result_type=result_type,
        value=detected_event,
        logs=[prompt, llm_response],
        metadata={
            "api_call_time": api_call_time,
            "evaluation_source": evaluation_source,
            "llm_call": {
                "model": model_name,
                "prompt": prompt,
                "llm_output": llm_response,
                "api_call_time": api_call_time,
                "evaluation_source": evaluation_source,
            },
        },
    )


async def evaluate_task(
    message: Message,
    few_shot_min_number_of_examples: int = 5,
    few_shot_max_number_of_examples: int = 10,
    model: str = "openai:gpt-4-1106-preview",
) -> JobResult:
    """
    Evaluate a task:
    - If there are not enough examples, use the zero shot expensive classifier
    - If there are enough examples, use the cheaper few shot classifier

    Message.metadata = {
        "successful_examples": [{input, output, flag}],
        "unsuccessful_examples": [{input, output, flag}],
        "system_prompt": str,
    }
    """
    from phospho.utils import fits_in_context_window

    # Check if some Env variables override the default model and LLM provider
    provider, model_name = get_provider_and_model(model)
    async_openai_client = get_async_client(provider)

    successful_examples = message.metadata.get("successful_examples", [])
    unsuccessful_examples = message.metadata.get("unsuccessful_examples", [])
    system_prompt = message.metadata.get("system_prompt", None)

    assert isinstance(successful_examples, list), "successful_examples is not a list"
    assert isinstance(
        unsuccessful_examples, list
    ), "unsuccessful_examples is not a list"

    # 32k is the max input length for gpt-4-1106-preview, we remove 1k to be safe
    # TODO : Make this adaptative to model name
    max_tokens_input_lenght = 128 * 1000 - 1000
    merged_examples = []
    min_number_of_examples = min(len(successful_examples), len(unsuccessful_examples))

    for i in range(0, min_number_of_examples):
        merged_examples.append(successful_examples[i])
        merged_examples.append(unsuccessful_examples[i])

    # Shuffle the examples
    random.shuffle(merged_examples)

    # Additional metadata
    api_call_time: Optional[float] = None
    llm_call: Optional[dict] = None

    async def zero_shot_evaluation(
        prompt: str,
        model_name: str = os.getenv("MODEL_ID", "gpt-4-1106-preview"),
    ) -> Optional[Literal["success", "failure"]]:
        """
        Call the LLM API to get a zero shot classification of a task
        as a success or a failure.
        """
        nonlocal api_call_time
        nonlocal llm_call

        if not fits_in_context_window(prompt, max_tokens_input_lenght):
            logger.error("The prompt does not fit in the context window")
            # TODO : Fall back to a bigger model
            return None

        logger.debug(f"Running zero shot evaluation with model {model_name}")

        start_time = time.time()
        response = await async_openai_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
            max_tokens=5,  # We only need a small output
        )

        llm_response = response.choices[0].message.content
        api_call_time = time.time() - start_time

        llm_call = {
            "model": model_name,
            "prompt": prompt,
            "llm_output": llm_response,
            "api_call_time": api_call_time,
            "evaluation_source": "phospho-4",
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

    async def few_shot_evaluation(
        message: Message,
        successful_examples: list,  # {input, output, flag}
        unsuccessful_examples: list,  # {input, output}
    ) -> Optional[Literal["success", "failure"]]:
        """
        Few shot classification of a task using Cohere classification API
        We balance the number of examples for each category (success, failure).
        We use the most recent examples for the two categories
        (the ones with the smaller index in the list)
        """
        import cohere
        from cohere.responses.classify import Example

        co = cohere.AsyncClient(config.COHERE_API_KEY, timeout=40)

        half_few_shot_max = few_shot_max_number_of_examples // 2
        # Truncate the examples to the max number of examples
        if len(successful_examples) > half_few_shot_max:
            successful_examples = successful_examples[:half_few_shot_max]
            logger.debug(
                f"truncated successful examples to {half_few_shot_max} examples"
            )

        if len(unsuccessful_examples) > half_few_shot_max:
            unsuccessful_examples = unsuccessful_examples[:half_few_shot_max]
            logger.debug(
                f"truncated unsuccessful examples to {half_few_shot_max} examples"
            )

        # Format the examples
        examples = []
        for example in successful_examples:
            text_prompt = f"User: {example['input']}\nAssistant: {example['output']}"
            examples.append(Example(text_prompt, "success"))
        for example in unsuccessful_examples:
            text_prompt = f"User: {example['input']}\nAssistant: {example['output']}"
            examples.append(Example(text_prompt, "failure"))

        # Shuffle the examples
        random.shuffle(examples)

        if len(examples) > few_shot_max_number_of_examples:
            examples = examples[:few_shot_max_number_of_examples]
            logger.debug(
                f"Truncated examples to {few_shot_max_number_of_examples} examples"
            )

        # Build the prompt to classify
        text_prompt_to_classify = message.transcript(with_role=True)
        inputs = [text_prompt_to_classify]  # TODO : batching later?

        try:
            response = await co.classify(
                model="large",
                inputs=inputs,
                examples=examples,
            )
        except Exception as e:
            await co.close()  # Close the connection before raising the exception
            raise e

        # Close the connection
        await co.close()
        flag = response.classifications[0].predictions[0]
        confidence = response.classifications[0].confidences[0]
        # TODO : add check on confidence ?
        logger.debug(f"few_shot_eval flag : {flag}, confidence : {confidence}")
        if flag in ["success", "failure"]:
            return flag
        else:
            raise Exception("The flag is not success or failure")

    def build_zero_shot_prompt(
        message: Message, system_prompt: Optional[str] = None
    ) -> str:
        """
        Builds a zero shot prompt for the evaluation of a task.
        """
        # Zero shot mode
        logger.debug("Running eval in zero shot mode")

        # Build zero shot prompt
        prompt = """You are an impartial judge evaluating an interaction between a user and an assistant. \
        Your goal is to say if the assistant response to the user was good or bad."""

        if system_prompt:
            prompt += f"""An assistant behaviour is guided by its system prompt. A good assistant response follows \
                its system prompt. A bad assistant response disregards its system prompt. The system prompt of the assistant \
                is the following:
                [START SYSTEM PROMPT]
                {system_prompt}
                [END SYSTEM PROMPT]
            """
        else:
            # Assume a generic system prompt
            # TODO : Use the project settings and events suggestions to infer a system prompt
            prompt += """A good assistant is helpful, concise, precise, entertaining, sharp, to the point, direct, agreeable.
            A bad assistant is pointless, verbose, boring, off-topic, inaccurate, unhelpful, misleading, confusing.
            """

        # If there is a previous task, add it to the prompt
        if len(message.previous_messages) > 0:
            prompt += f"""A good assistant remembers previous interactions and gives in context answers.
            A bad assistant ignores the context of the conversation and responds out of touch. 
            The previous interaction between the user and the assistant was the following:
            [START PREVIOUS INTERACTION]
            {message.previous_messages_transcript(with_role=True)}
            [END PREVIOUS INTERACTION]
            """

        prompt += f"""Given the best of your knowledge, evaluate the following interaction between the user and the assistant:
        [START INTERACTION]
        {message.transcript(with_role=True)}
        [END INTERACTION]

        Respond with only one word: success if the assistant response was good, failure if the assistant response was bad.
        """
        return prompt

    if len(merged_examples) < few_shot_min_number_of_examples:
        # Zero shot mode
        prompt = build_zero_shot_prompt(message, system_prompt)
        flag = await zero_shot_evaluation(prompt, model_name=model_name)
    else:
        # Few shot mode
        logger.debug(
            f"Running eval in few shot mode with Cohere classifier and {len(merged_examples)} examples"
        )
        prompt = None
        try:
            flag = await few_shot_evaluation(
                message=message,
                successful_examples=successful_examples,
                unsuccessful_examples=unsuccessful_examples,
            )
        except Exception as e:
            logger.error(
                f"Error in few shot evaluation (falling back to zero shot mode) : {e}"
            )
            prompt = build_zero_shot_prompt(message, system_prompt)
            flag = await zero_shot_evaluation(prompt, model_name=model_name)

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
    message: Message, model: Optional[str] = "openai:gpt-3.5-turbo-0613", tokenizer=None
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
