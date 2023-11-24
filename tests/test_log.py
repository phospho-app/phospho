import pytest

import phospho
from openai.types.chat import ChatCompletion, ChatCompletionMessage
from openai.types.completion_usage import CompletionUsage
from openai.types.chat.chat_completion import Choice


def test_logging():
    phospho.init()

    query = {
        "messages": [{"role": "user", "content": "Say hi !"}],
        "model": "gpt-3.5-turbo",
    }
    response = ChatCompletion(
        id="chatcmpl-8ONC0iiWZXmkddojmWfR6w3aHdTsu",
        choices=[
            Choice(
                finish_reason="stop",
                index=0,
                message=ChatCompletionMessage(
                    content="Hello! How can I assist you today?",
                    role="assistant",
                    function_call=None,
                    tool_calls=None,
                ),
            )
        ],
        created=1700819716,
        model="gpt-3.5-turbo-0613",
        object="chat.completion",
        system_fingerprint=None,
        usage=CompletionUsage(completion_tokens=9, prompt_tokens=10, total_tokens=19),
    )

    log_content = phospho.log(input=query, output=response)

    assert log_content["input"] == "user: Say hi !"
    assert log_content["output"] == "assistant: Hello! How can I assist you today?"
    assert log_content["session_id"] is not None, "default session_id should be created"
    old_session_id = log_content["session_id"]

    log_content = phospho.log(input=query, output=response)
    new_session_id = log_content["session_id"]
    assert (
        new_session_id == old_session_id
    ), "session_id should be preserved between 2 continuous calls"
