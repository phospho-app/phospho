import logging
import time

import phospho
import pytest
from openai.types.chat import ChatCompletion, ChatCompletionChunk, ChatCompletionMessage
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_chunk import Choice as chunk_Choice
from openai.types.chat.chat_completion_chunk import ChoiceDelta
from openai.types.completion_usage import CompletionUsage

logger = logging.getLogger(__name__)

MOCK_OPENAI_QUERY = {
    "messages": [{"role": "user", "content": "Say hi !"}],
    "model": "gpt-3.5-turbo",
}

MOCK_OPENAI_RESPONSE = ChatCompletion(
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

MOCK_OPENAI_STREAM_RESPONSE = [
    ChatCompletionChunk(
        id="chatcmpl-8PWAOdCT73H5XUum52ny3NHnw2ZQx",
        choices=[
            chunk_Choice(
                delta=ChoiceDelta(
                    content="Hello", function_call=None, role=None, tool_calls=None
                ),
                finish_reason=None,
                index=0,
            )
        ],
        created=1701092540,
        model="gpt-3.5-turbo-0613",
        object="chat.completion.chunk",
        system_fingerprint=None,
    ),
    ChatCompletionChunk(
        id="chatcmpl-8PWAOdCT73H5XUum52ny3NHnw2ZQx",
        choices=[
            chunk_Choice(
                delta=ChoiceDelta(
                    content=" you",
                    function_call=None,
                    role=None,
                    tool_calls=None,
                ),
                finish_reason=None,
                index=0,
            )
        ],
        created=1701092540,
        model="gpt-3.5-turbo-0613",
        object="chat.completion.chunk",
        system_fingerprint=None,
    ),
    ChatCompletionChunk(
        id="chatcmpl-8PWAOdCT73H5XUum52ny3NHnw2ZQx",
        choices=[
            chunk_Choice(
                delta=ChoiceDelta(
                    content="!", function_call=None, role=None, tool_calls=None
                ),
                finish_reason=None,
                index=0,
            )
        ],
        created=1701092540,
        model="gpt-3.5-turbo-0613",
        object="chat.completion.chunk",
        system_fingerprint=None,
    ),
    ChatCompletionChunk(
        id="chatcmpl-8PWAOdCT73H5XUum52ny3NHnw2ZQx",
        choices=[
            chunk_Choice(
                delta=ChoiceDelta(
                    content=None, function_call=None, role=None, tool_calls=None
                ),
                finish_reason="stop",
                index=0,
            )
        ],
        created=1701092540,
        model="gpt-3.5-turbo-0613",
        object="chat.completion.chunk",
        system_fingerprint=None,
    ),
]


def test_log_sync():
    phospho.init(tick=0.05, raise_error_on_fail_to_send=True)

    # Log a string
    log_content = phospho.log(
        input="Say hi !", output="Hello! How can I assist you today?"
    )

    # Log a list
    log_content = phospho.log(
        input=["Say hi !", "Say hi again !"],
        output=[
            "Hello! How can I assist you today?",
            "Hello! How can I assist you today?",
        ],
    )

    # Log a dict
    log_content = phospho.log(
        input={"Say hi !": "Say hi again !"},
        output={
            "Hello! How can I assist you today?": "Hello! How can I assist you today?"
        },
    )

    # Log openai (extraction)
    query = MOCK_OPENAI_QUERY
    response = MOCK_OPENAI_RESPONSE

    log_content = phospho.log(input=query, output=response)

    assert log_content["input"] == "Say hi !"
    assert log_content["output"] == "Hello! How can I assist you today?"
    assert (
        log_content["session_id"] is not None
    ), "A default session_id should be set by the logger"
    assert log_content["prompt_tokens"] == 10
    assert log_content["completion_tokens"] == 9
    assert log_content["total_tokens"] == 19

    # TODO : Validate that the connection was successful

    time.sleep(0.1)


def test_wrap():
    phospho.init(tick=0.05, raise_error_on_fail_to_send=True)

    # No streaming
    def fake_openai_call_no_stream(model, messages, stream: bool = False):
        return MOCK_OPENAI_RESPONSE

    response = phospho.wrap(fake_openai_call_no_stream)(
        model=MOCK_OPENAI_QUERY["model"],
        messages=MOCK_OPENAI_QUERY["messages"],
    )
    assert response == MOCK_OPENAI_RESPONSE
    response = phospho.wrap(fake_openai_call_no_stream)(
        model=MOCK_OPENAI_QUERY["model"],
        messages=MOCK_OPENAI_QUERY["messages"],
        stream=False,
    )
    assert response == MOCK_OPENAI_RESPONSE

    # Streaming

    def fake_openai_call_stream(model, messages, stream: bool = True):
        for stream_response in MOCK_OPENAI_STREAM_RESPONSE:
            yield stream_response

    response = phospho.wrap(fake_openai_call_stream)(
        model=MOCK_OPENAI_QUERY["model"],
        messages=MOCK_OPENAI_QUERY["messages"],
        stream=True,
    )
    # Streamed content should be the same
    for r, groundtruth_r in zip(response, MOCK_OPENAI_STREAM_RESPONSE):
        assert r == groundtruth_r

    time.sleep(0.1)


def test_log_list_of_messages():
    """
    Log a list of RoleContentMessages (OpenAI format)
    """
    phospho.init(tick=0.05, raise_error_on_fail_to_send=True)

    conversation = [
        {
            "role": "system",
            "content": "Answer yes",
        },
        {
            "role": "user",
            "content": "Say hi !",
        },
        {
            "role": "assistant",
            "content": "Hello",
        },
    ]
    log = phospho.log(
        input=conversation,
        output=conversation,
    )
    assert log["input"] == "Say hi !"
    assert log["output"] == "Hello"
    assert log["system_prompt"] == "Answer yes"

    # Multiple system prompts
    conversation = [
        {
            "role": "system",
            "content": "Answer yes",
        },
        {
            "role": "system",
            "content": "Never say hi",
        },
        {
            "role": "user",
            "content": "Say hi !",
        },
        {
            "role": "assistant",
            "content": "Good morning",
        },
    ]
    log = phospho.log(
        input=conversation,
        output=conversation,
    )
    assert log["input"] == "Say hi !"
    assert log["output"] == "Good morning"
    # Multiple system prompts are concatenated
    assert log["system_prompt"] == "Answer yes\nNever say hi"

    # Succession of multiple assistant messages
    conversation = [
        {
            "role": "assistant",
            "content": "Hello",
        },
        {
            "role": "user",
            "content": "Hi",
        },
        {
            "role": "assistant",
            "content": "How are you?",
        },
        {
            "role": "assistant",
            "content": "Are you fine?",
        },
    ]
    log = phospho.log(input=conversation, output=conversation)
    assert log["input"] == "Hi"
    assert log["output"] == "How are you?\nAre you fine?"

    # Succession of multiple user messages
    conversation = [
        {
            "role": "user",
            "content": "Hello",
        },
        {
            "role": "user",
            "content": "Hi",
        },
        {
            "role": "assistant",
            "content": "How are you?",
        },
        {
            "role": "assistant",
            "content": "Are you fine?",
        },
    ]
    log = phospho.log(
        input=conversation,
        output=conversation,
    )
    assert log["input"] == "Hello\nHi"
    assert log["output"] == "How are you?\nAre you fine?"

    # Multiple system prompts without user or assistant messages
    conversation = [
        {
            "role": "system",
            "content": "Hello",
        },
        {
            "role": "system",
            "content": "Hi",
        },
    ]
    log = phospho.log(
        input=conversation,
    )
    assert log["system_prompt"] == "Hello\nHi"
    assert log["input"] == ""
    assert log["output"] is None

    time.sleep(0.1)


def test_stream():
    phospho.init(tick=0.05, raise_error_on_fail_to_send=True)

    # Streaming, sync

    def fake_openai_call_stream(model, messages, stream: bool = True):
        for stream_response in MOCK_OPENAI_STREAM_RESPONSE:
            yield stream_response

    class FakeStream:
        def __init__(self, model, messages, stream: bool = True):
            self._iterator = fake_openai_call_stream(model, messages, stream)

        def __iter__(self):
            for item in self._iterator:
                yield item

        def __next__(self):
            return self._iterator.__next__()

    query = {
        "model": MOCK_OPENAI_QUERY["model"],
        "messages": MOCK_OPENAI_QUERY["messages"],
        "stream": True,
    }
    response = FakeStream(**query)
    log = phospho.log(input=query, output=response, stream=True)
    task_id = log["task_id"]
    # Streamed content should be the same
    i = 0
    for r in response:
        groundtruth_r = MOCK_OPENAI_STREAM_RESPONSE[i]
        assert r == groundtruth_r
        assert (
            task_id in phospho.log_queue.events.keys()
        ), f"{task_id} not found in the log_queue.events: {phospho.log_queue.events.keys()}, round {i}"
        raw_output = phospho.log_queue.events[task_id].content["raw_output"]
        if isinstance(raw_output, list):
            assert raw_output[-1] == groundtruth_r.model_dump()
        else:
            assert raw_output == groundtruth_r.model_dump()
        i += 1

    # TODO : Validate that the connection was successful
    time.sleep(0.1)


@pytest.mark.asyncio
async def test_async_stream():
    phospho.init(tick=0.05, raise_error_on_fail_to_send=True)

    query = {
        "model": MOCK_OPENAI_QUERY["model"],
        "messages": MOCK_OPENAI_QUERY["messages"],
        "stream": True,
    }

    # This async class is similar to the OpenAI one
    class FakeAsyncStream:
        def __init__(self, model, messages, stream: bool = True):
            self._values = MOCK_OPENAI_STREAM_RESPONSE
            self.i = 0

        def __aiter__(self):
            return self

        async def __anext__(self):
            if self.i >= len(self._values):
                raise StopAsyncIteration
            self.i += 1
            return self._values[self.i - 1]

    async def test_once():
        response = FakeAsyncStream(**query)

        log = phospho.log(input=query, output=response, stream=True)

        task_id = log["task_id"]
        assert task_id not in phospho.log_queue.events.keys()

        # Streamed content should be the same
        i = 0
        async for r in response:
            resp = r
            assert i < len(MOCK_OPENAI_STREAM_RESPONSE), str(resp)
            groundtruth_r = MOCK_OPENAI_STREAM_RESPONSE[i]
            assert r == groundtruth_r
            # Log queue has been flushed at the last response
            if i < len(MOCK_OPENAI_STREAM_RESPONSE) - 1:
                log_content = phospho.log_queue.events[log["task_id"]].content
                raw_output = log_content["raw_output"]
                if isinstance(raw_output, list):
                    assert raw_output[-1] == groundtruth_r.model_dump()
                else:
                    assert raw_output == groundtruth_r.model_dump()
            i += 1
        assert i <= len(MOCK_OPENAI_STREAM_RESPONSE), str(r)
        return task_id

    # Test multiple times
    # task_id_1 = await test_once()
    # task_id_2 = await test_once()
    # assert task_id_1 != task_id_2

    # Test with another kind of generator

    async def fake_async_openai_call_stream(model, messages, stream: bool = True):
        for stream_response in MOCK_OPENAI_STREAM_RESPONSE:
            logger.debug(stream_response)
            yield stream_response

    class MutableGenerator:
        def __init__(self, generator):
            self.generator = generator

        # def __iter__(self):
        #     return self

        def __aiter__(self):
            return self

        # def __next__(self):
        #     return self.generator.__next__()

        def __anext__(self):
            return self.generator.__anext__()

    response = MutableGenerator(fake_async_openai_call_stream(**query))

    log = phospho.log(input=query, output=response, stream=True)
    task_id = log["task_id"]
    # Nothing in log queue yet
    assert task_id not in phospho.log_queue.events.keys()
    # Streamed content should be the same
    i = 0
    async for r in response:
        resp = r
        assert i < len(MOCK_OPENAI_STREAM_RESPONSE), str(resp)
        groundtruth_r = MOCK_OPENAI_STREAM_RESPONSE[i]
        assert r == groundtruth_r
        # Log queue has been flushed at the last response
        if i < len(MOCK_OPENAI_STREAM_RESPONSE) - 1:
            assert (
                task_id in phospho.log_queue.events.keys()
            ), f"{task_id} not found in the log_queue.events: {phospho.log_queue.events.keys()}"
            log_content = phospho.log_queue.events[log["task_id"]].content
            raw_output = log_content["raw_output"]
            if isinstance(raw_output, list):
                assert raw_output[-1] == groundtruth_r.model_dump()
            else:
                assert raw_output == groundtruth_r.model_dump()
        i += 1
    assert i <= len(MOCK_OPENAI_STREAM_RESPONSE), str(r)

    time.sleep(0.1)
