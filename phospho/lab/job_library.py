"""
Collection of jobs for the laboratory. 
Each job is a function that takes a message and a set of parameters and returns a result.
The result is a JobResult object.
"""

import random
from typing import List, Literal, Optional, Tuple, cast
from .models import Message, JobResult
from app import config

import time
import openai
import logging

logger = logging.getLogger(__name__)

# TODO: Turn this into a shared resource managed by the Workload
openai_client = openai.Client()
async_openai_client = openai.AsyncClient()


def prompt_to_bool(
    message: Message,
    prompt: str,
    message_context: Optional[str] = None,
    format_kwargs: Optional[dict] = None,
    model: str = "gpt-3.5-turbo",
) -> JobResult:
    """
    Runs a prompt on a message and returns a boolean result.
    """
    if format_kwargs is None:
        format_kwargs = {}

    formated_prompt = prompt.format(
        message_content=message.content,
        message_context=message_context,
        **format_kwargs,
    )
    response = openai_client.chat.completions.create(
        model=model,
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

    # Cast the response to a bool
    if response.choices[0].message.content is None:
        bool_response = False
    else:
        bool_response = response.choices[0].message.content.lower() == "true"

    return JobResult(
        job_name="prompt_to_bool",
        result_type="bool",
        value=bool_response,
        logs=[formated_prompt, response.choices[0].message.content],
    )


def prompt_to_literal(
    message: Message,
    prompt: str,
    output_literal: List[str],
    message_context: Optional[str] = None,
    format_kwargs: Optional[dict] = None,
    model: str = "gpt-3.5-turbo",
) -> JobResult:
    """
    Runs a prompt on a message and returns a str from the list ouput_literal.
    """
    if format_kwargs is None:
        format_kwargs = {}

    formated_prompt = prompt.format(
        message_content=message.content,
        message_context=message_context,
        **format_kwargs,
    )
    response = openai_client.chat.completions.create(
        model=model,
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
                job_name="prompt_to_literal",
                result_type="literal",
                value=response_content,
            )
        # Greedy: Check if the response contains one of the output_literal
        for literal in output_literal:
            if literal in response_content:
                return JobResult(
                    job_name="prompt_to_literal",
                    result_type="literal",
                    value=response_content,
                )

    return JobResult(
        job_name="prompt_to_literal",
        result_type="literal",
        value=literal_response,
        logs=[formated_prompt, response.choices[0].message.content],
    )


async def event_detection(
    task_transcript: str,
    event_name: str,
    event_description: str,
    task_context_transcript: str = "",
    store_llm_call: bool = True,
    org_id: Optional[str] = None,
    model: str = "gpt-3.5-turbo",
) -> Tuple[bool, str]:
    # Build the prompt
    if task_context_transcript == "":
        prompt = f"""
You are classifying an interaction between an end user and an assistant. The assistant is a chatbot that can perform tasks for the end user and answer his questions. 
The assistant might make some mistakes or not be useful.
The event you are looking for is : {event_description}. The name of the event is : {event_name}

Here is the transcript of the interaction:
[START INTERACTION]
{task_transcript}
[END INTERACTION]

You have to say if the event is present in the transcript or not. Respond with only one word, True or False.
    """
    else:
        prompt = f"""
You are classifying an interaction between an end user and an assistant. The assistant is a chatbot that can perform tasks for the end user and answer his questions. 
The assistant might make some mistakes or not be useful.
The event you are looking for is : {event_description} 
The name of the event is : {event_name}

Here is the previous messages of the conversation before the interaction to help you better understand the extract:
[START CONTEXT]
{task_context_transcript}
[END CONTEXT]

Here is the transcript of the interaction:
[START INTERACTION]
{task_transcript}
[END INTERACTION]

You have to say if the event is present in the transcript or not. Respond with only one word, True or False.
    """

    logger.debug(f"event_detection prompt : {prompt}")

    # Call the API
    start_time = time.time()

    try:
        response = await async_openai_client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=1,
            temperature=0,
        )
    except Exception as e:
        logger.error(f"event_detection call to OpenAI API failed : {e}")
        return False, "error"

    api_call_time = time.time() - start_time

    logger.debug(f"event_detection call to OpenAI API ({api_call_time} sec)")

    # Parse the response
    llm_response = response.choices[0].message.content
    logger.debug(f"event_detection llm_response : {llm_response}")
    if llm_response is not None:
        llm_response = llm_response.strip()

    # Validate the output
    if llm_response == "True" or llm_response == "true":
        detected_event = True
    elif llm_response == "False" or llm_response == "false":
        detected_event = False
    else:
        raise Exception(
            f"The classifier did not return True or False (got : {llm_response})"
        )

    # Identifier of the source of the evaluation, with the version of the model if phospho
    evaluation_source = "phospho-4"

    # TODO : Make it so that this works again
    # Store the query and the response in the database
    # if store_llm_call:
    #     # WARNING : adds latency
    #     # Create the llm_call object from the pydantic model
    #     llm_call_obj = LlmCall(
    #         model=model,
    #         prompt=prompt,
    #         llm_output=llm_response,
    #         api_call_time=api_call_time,
    #         evaluation_source=evaluation_source,
    #         org_id=org_id,
    #     )
    #     mongo_db = await get_mongo_db()
    #     mongo_db["llm_calls"].insert_one(llm_call_obj.model_dump())

    logger.debug(f"event_detection detected event {event_name} : {detected_event}")
    # Return the result
    return detected_event, evaluation_source


async def evaluate_task(
    task_input: str,
    task_output: str,
    previous_task_input: str = "",
    previous_task_output: str = "",
    successful_examples: list = [],  # {input, output, flag}
    unsuccessful_examples: list = [],  # {input, output}
    org_id: Optional[str] = None,
    model_name: str = "gpt-4-1106-preview",
    few_shot_min_number_of_examples: int = 5,
    few_shot_max_number_of_examples: int = 10,
) -> Optional[Literal["success", "failure"]]:
    """
    We expect the more relevant examples to be at the beginning of the list (cf db query)
    """
    from phospho.utils import fits_in_context_window

    async def get_flag(
        prompt: str,
        store_llm_call: bool = True,
        model_name: str = "gpt-4-1106-preview",
        org_id: Optional[str] = None,
    ) -> Optional[Literal["success", "failure"]]:
        response = await async_openai_client.chat.completions.create(
            model=model_name,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ],
            temperature=0,
        )

        # Call the API
        start_time = time.time()

        llm_response = response.choices[0].message.content

        # TODO : Fix this
        # Store the query and the response in the database
        # if store_llm_call:
        #     # WARNING : adds latency
        #     # Create the llm_call object from the pydantic model
        #     llm_call_obj = LlmCall(
        #         model=model_name,
        #         prompt=prompt,
        #         llm_output=llm_response,
        #         api_call_time=time.time() - start_time,
        #         evaluation_source=config.EVALUATION_SOURCE,
        #         org_id=org_id,
        #     )
        #     mongo_db = await get_mongo_db()
        #     await mongo_db["llm_calls"].insert_one(llm_call_obj.model_dump())

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

    async def few_shot_eval(
        task_input: str,
        task_output: str,
        successful_examples: list = [],  # {input, output, flag}
        unsuccessful_examples: list = [],  # {input, output}
    ) -> Optional[Literal["success", "failure"]]:
        """
        Few shot classification of a task using Cohere classification API
        We want to have the same number of successful examples and unsuccessful examples
        We want to have the most recent examples for the two categories (the ones with the smaller index in the list)
        """
        import cohere
        from cohere.responses.classify import Example

        co = cohere.AsyncClient(config.COHERE_API_KEY, timeout=40)

        # Truncate the examples to the max number of examples
        if len(successful_examples) > few_shot_max_number_of_examples // 2:
            successful_examples = successful_examples[
                : few_shot_max_number_of_examples // 2
            ]
            logger.debug(
                f"truncated successful examples to {few_shot_max_number_of_examples // 2} examples"
            )

        if len(unsuccessful_examples) > few_shot_max_number_of_examples // 2:
            unsuccessful_examples = unsuccessful_examples[
                : few_shot_max_number_of_examples // 2
            ]
            logger.debug(
                f"truncated unsuccessful examples to {few_shot_max_number_of_examples // 2} examples"
            )

        # Build the examples
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
                f"truncated examples to {few_shot_max_number_of_examples} examples"
            )

        # Build the prompt to classify
        text_prompt_to_classify = f"User: {task_input}\nAssistant: {task_output}"
        inputs = [text_prompt_to_classify]  # TODO : batching later?

        response = await co.classify(
            model="large",
            inputs=inputs,
            examples=examples,
        )
        await co.close()  # the AsyncClient client should be closed when done

        flag = response.classifications[0].prediction
        confidence = response.classifications[0].confidence

        # TODO : add check on confidence ?

        logger.debug(f"few_shot_eval flag : {flag}, confidence : {confidence}")

        if flag in ["success", "failure"]:
            return flag
        else:
            raise Exception("The flag is not success or failure")

    # Get the model max input token length
    max_tokens_input_lenght = (
        128 * 1000 - 1000
    )  # 32k is the max input length for gpt-4-1106-preview, we remove 1k to be safe

    merged_examples = []

    min_number_of_examples = min(len(successful_examples), len(unsuccessful_examples))

    for i in range(0, min_number_of_examples):
        merged_examples.append(successful_examples[i])
        merged_examples.append(unsuccessful_examples[i])

    # Shuffle the examples
    random.shuffle(merged_examples)

    # Build the prompt

    if len(merged_examples) < few_shot_min_number_of_examples:
        # Zero shot mode
        logger.debug("running eval in zero shot mode")

        # Build zero shot prompt

        # If there is a previous task, add it to the prompt
        if previous_task_input != "" and previous_task_output != "":
            prompt = f"""
            You are evaluating an interaction between a user and an assistant. 
            Your goal is to determine if the assistant was helpful or not to the user.

            Here is the previous interaction between the user and the assistant:
            [START PREVIOUS INTERACTION]
            User: {previous_task_input}
            Assistant: {previous_task_output}
            [END PREVIOUS INTERACTION]

            Here is the interaction between the user and the assistant you need to evaluate:
            [START INTERACTION]
            User: {task_input}
            Assistant: {task_output}
            [END INTERACTION]

            Respond with only one word, success if the assistant was helpful, failure if not.
            """
        else:
            prompt = f"""
            You are an impartial judge evaluating an interaction between a user and an assistant. 
            Your goal is to determine if the assistant was helpful or not to the user.

            Here is the interaction between the user and the assistant:
            [START INTERACTION]
            User: {task_input}
            Assistant: {task_output}
            [END INTERACTION]

            Respond with only one word, success if the assistant was helpful, failure if not.
            """

        # Check the context window size
        if fits_in_context_window(prompt, max_tokens_input_lenght):
            # Call the API
            flag = await get_flag(prompt, org_id=org_id)
            return flag

        else:
            logger.error("The prompt does not fit in the context window")
            # flag = "undefined"
            flag = None
            return flag

    else:
        # Few shot mode, we have enough examples to use them
        flag = await few_shot_eval(
            task_input,
            task_output,
            successful_examples=successful_examples,
            unsuccessful_examples=unsuccessful_examples,
        )

        logger.debug(
            f"running eval in few shot mode with Cohere classifier and {len(merged_examples)} examples"
        )

        return flag
