import pytest
import phospho

from openai import OpenAI


def test_tracing():
    phospho.init(
        tick=0.05,
        raise_error_on_fail_to_send=True,
        tracing=True,
        base_url="http://127.0.0.1:8000",
    )

    # Make an API call
    openai_client = OpenAI()
    messages = [{"role": "user", "content": "Say hi"}]
    response = openai_client.chat.completions.create(
        messages=messages,
        model="gpt-4o-mini",
        max_tokens=1,
    )

    phospho.log(
        input=messages,
        output=response,
    )
