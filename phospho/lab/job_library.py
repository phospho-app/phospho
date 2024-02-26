"""
Collection of jobs for the laboratory. 
Each job is a function that takes a message and a set of parameters and returns a result.
The result is a JobResult object.
"""

from typing import List, Optional, Tuple
from .models import Message, JobResult

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
