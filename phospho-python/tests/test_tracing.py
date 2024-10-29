import pytest
import phospho

from openai import OpenAI


def test_tracing():
    phospho.init(
        tick=0.05,
        raise_error_on_fail_to_send=True,
        base_url="http://127.0.0.1:8000",
        tracing=True,
    )

    openai_client = OpenAI()
    messages = [
        {"role": "system", "content": "Obey"},
        {"role": "user", "content": "Say hi"},
    ]

    # Implicit syntax
    response = openai_client.chat.completions.create(
        messages=messages,
        model="gpt-4o-mini",
        max_tokens=1,
    )
    # Inspect phospho.spans_to_export
    assert len(phospho.spans_to_export) == 1
    phospho.log(
        input=messages,
        output=response,
    )

    # Context syntax
    with phospho.tracer() as tracer:
        # Make an API call
        response = openai_client.chat.completions.create(
            messages=messages,
            model="gpt-4o-mini",
            max_tokens=1,
        )
        # Inspect tracer.spans_to_export
        assert len(tracer.spans_to_export) == 1
        log_content = phospho.log(
            input=messages,
            output=response,
        )
        # Check that the task_id and session_id are correctly set
        assert log_content["task_id"] == tracer.task_id
        assert log_content["session_id"] == tracer.session_id

    # Decorator syntax. This is just a syntactic sugar for the context syntax
    @phospho.tracer()
    def my_function():
        # Make an API call
        response = openai_client.chat.completions.create(
            messages=messages,
            model="gpt-4o-mini",
            max_tokens=1,
        )
        phospho.log(
            input=messages,
            output=response,
        )

    my_function()
