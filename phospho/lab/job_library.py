"""
Collection of jobs for the laboratory. 
Each job is a function that takes a message and a set of parameters and returns a result.
The result is a JobResult object.
"""

from .models import Message, JobResult

import openai

openai_client = openai.Client()


def prompt_to_bool(
    message: Message,
    prompt: str,
    format_kwargs: dict,
) -> JobResult:
    """
    Returns a Tag with the result of the prompt.
    """
    response = openai_client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {
                "role": "user",
                "content": prompt.format(
                    message_content=message.content, **format_kwargs
                ),
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
    )
