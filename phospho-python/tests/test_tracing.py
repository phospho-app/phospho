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

    # Implicit syntax
    response = openai_client.chat.completions.create(
        messages=[
            {"role": "system", "content": "Obey"},
            {"role": "user", "content": "Say hi"},
        ],
        model="gpt-4o-mini",
        max_tokens=1,
    )
    # Inspect phospho.spans_to_export
    assert len(phospho.spans_to_export["global"]) == 1
    phospho.log(
        system_prompt="Obey",
        input="Say hi",
        output=response,
    )

    # Context syntax
    with phospho.tracer() as context_name:
        # Make an API call
        messages = [{"role": "user", "content": "Say good bye"}]
        openai_client.chat.completions.create(
            messages=messages,
            model="gpt-4o-mini",
            max_tokens=1,
        )
        # Make a second and a third
        openai_client.chat.completions.create(
            messages=messages,
            model="gpt-4o-mini",
            max_tokens=1,
        )
        response = openai_client.chat.completions.create(
            messages=messages,
            model="gpt-4o-mini",
            max_tokens=1,
        )
        # Inspect tracer.spans_to_export
        # assert len(phospho.spans_to_export[context_name]) == 3
        log_content = phospho.log(
            input="Say good bye",
            output=response,
        )
        # Check that the task_id and session_id are correctly set
        # assert log_content["task_id"] == phospho.task_id_override
        # assert log_content["session_id"] == phospho.session_id_override

    # Decorator syntax. This is just a syntactic sugar for the context syntax
    @phospho.trace()
    def my_function():
        # Make an API call
        response = openai_client.chat.completions.create(
            messages=[{"role": "user", "content": "Say a joke"}],
            model="gpt-4o-mini",
            max_tokens=1,
        )
        phospho.log(
            input="Say a joke",
            output=response,
        )

    my_function()

    # Another tracing method, add intermediate steps
    phospho.log(
        input="Say bossman",
        output="Bossman",
        intermediate_logs=[{"some_data": "very important"}],
    )

    phospho.flush()
