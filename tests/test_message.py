# test_message.py

import pytest
from phospho import Message  # Replace `your_script_name` with the actual filename

@pytest.fixture
def message_instance():
    prompt = "Enter your message:"
    payload = {"text": "Hello, world!"}
    metadata = {"timestamp": "2023-07-26 12:34:56", "user_id": "12345"}

    return Message(prompt=prompt, payload=payload, metadata=metadata)

def test_message_constructor():
    prompt = "Enter your message:"
    payload = {"text": "Hello, world!"}
    metadata = {"timestamp": "2023-07-26 12:34:56", "user_id": "12345"}

    msg = Message(prompt=prompt, payload=payload, metadata=metadata)

    assert msg.prompt == prompt
    assert msg.payload == payload
    assert msg.metadata == metadata

def test_message_constructor_with_empty_values():
    empty_prompt = ""
    empty_payload = {}
    empty_metadata = {}

    msg = Message(prompt=empty_prompt, payload=empty_payload, metadata=empty_metadata)

    assert msg.prompt == empty_prompt
    assert msg.payload == empty_payload
    assert msg.metadata == empty_metadata

def test_message_constructor_with_all_empty_values():
    empty_prompt = ""
    empty_payload = {}
    empty_metadata = {}

    msg = Message(prompt=empty_prompt, payload=empty_payload, metadata=empty_metadata)

    assert msg.prompt == empty_prompt
    assert msg.payload == empty_payload
    assert msg.metadata == empty_metadata
