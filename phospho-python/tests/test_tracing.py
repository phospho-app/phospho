import pytest
import phospho

from openai import OpenAI


def test_context_tracing():
    phospho.init(
        tick=0.05,
        raise_error_on_fail_to_send=True,
        base_url="http://127.0.0.1:8000",
        tracing=True,
    )

    openai_client = OpenAI()

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


def test_tracing_steps():
    phospho.init(
        tick=0.05,
        raise_error_on_fail_to_send=True,
        base_url="http://127.0.0.1:8000",
        tracing=True,
    )

    phospho.log(
        input="Say bossman",
        output="Bossman",
        steps=[{"some_data": "very important"}],
    )
    phospho.log(
        input="Say bossmama",
        output="bossmama",
        steps=[{"other_data": "also important"}],
    )

    phospho.flush()


def test_tracing_global():
    """
    Global tracing: if you set tracing=True, this should trace
    all the API calls made by the OpenAI client.

    We link this ot phospho tasks every time there is a phospho.log :
    all previous API calls are linked to this task.
    """
    phospho.init(
        tick=0.05,
        raise_error_on_fail_to_send=True,
        base_url="http://127.0.0.1:8000",
        tracing=True,
    )

    openai_client = OpenAI()
    response = openai_client.chat.completions.create(
        messages=[
            {"role": "system", "content": "Obey"},
            {"role": "user", "content": "Say hi"},
        ],
        model="gpt-4o-mini",
        max_tokens=1,
    )
    phospho.log(
        system_prompt="Obey",
        input="Say hi",
        output=response,
    )

    response = openai_client.chat.completions.create(
        messages=[
            {"role": "system", "content": "Obey"},
            {"role": "user", "content": "Say hello"},
        ],
        model="gpt-4o-mini",
        max_tokens=1,
    )
    phospho.log(
        system_prompt="Obey",
        input="Say hello",
        output=response,
    )


def test_tracing_combined():
    phospho.init(
        tick=0.05,
        raise_error_on_fail_to_send=True,
        base_url="http://127.0.0.1:8000",
        tracing=True,  # Set tracing to True to track all GenAI call
    )
    openai_client = OpenAI()

    # Automatic tracing : GenAI spans are linked to the tasks logged
    response = openai_client.chat.completions.create(
        messages=[
            {"role": "system", "content": "Obey"},
            {"role": "user", "content": "Say hello"},
        ],
        model="gpt-4o-mini",
        max_tokens=1,
    )
    # Resolution from GenAI spans to tasks is based on timestamps.
    # Example: this task logged below will be linked to the openai call above.
    phospho.log(system_prompt="Obey", input="Say hello", output="Something else")

    # Explicit tracing : context blocks
    with phospho.tracer():  # Also works with @phospho.trace() syntax
        # Every GenAI span traced here will have a task_id set
        messages = [{"role": "user", "content": "Say good bye"}]
        openai_client.chat.completions.create(
            messages=messages,
            model="gpt-4o-mini",
            max_tokens=1,
        )
        phospho.log(input="Say good bye", output=response)

    # Manual tracing : add steps to phospho.log
    phospho.log(
        input="Say bossman",
        output="Bossman",
        steps=[{"some_data": "very important"}],
    )
    phospho.flush()
