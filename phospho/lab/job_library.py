"""
Collection of jobs for the laboratory. 
Each job is a function that takes a message and a set of parameters and returns a result.
The result is a JobResult object.
"""

from typing import List, Optional
from .models import Message, JobResult, JobConfig

import openai

# TODO: Turn this into a shared resource managed by the Workload
openai_client = openai.Client()


def prompt_to_bool(
    message: Message,
    prompt: str,
    message_context: Optional[str] = None,
    format_kwargs: Optional[dict] = None,
    model: str = "gpt-3.5-turbo",
    job_config: JobConfig = JobConfig(),
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
        model=job_config.model,
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
    job_config: JobConfig = JobConfig(),
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
        model=job_config.model,
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
