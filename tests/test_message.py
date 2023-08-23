# test_message.py

import pytest
from phospho import Message  # Replace `your_script_name` with the actual filename

@pytest.fixture
def message_instance():
    content = "Enter your message:"
    payload = {"text": "Hello, world!"}
    metadata = {"timestamp": "2023-07-26 12:34:56", "user_id": "12345"}

    return Message(content=content, payload=payload, metadata=metadata)

def test_message_constructor():
    content = "Enter your message:"
    payload = {"text": "Hello, world!"}
    metadata = {"timestamp": "2023-07-26 12:34:56", "user_id": "12345"}

    msg = Message(content=content, payload=payload, metadata=metadata)

    assert msg.content == content
    assert msg.payload == payload
    assert msg.metadata == metadata

def test_message_constructor_with_empty_values():
    empty_content = ""
    empty_payload = {}
    empty_metadata = {}

    msg = Message(content=empty_content, payload=empty_payload, metadata=empty_metadata)

    assert msg.content == empty_content
    assert msg.payload == empty_payload
    assert msg.metadata == empty_metadata

def test_message_constructor_with_all_empty_values():
    empty_content = ""
    empty_payload = {}
    empty_metadata = {}

    msg = Message(content=empty_content, payload=empty_payload, metadata=empty_metadata)

    assert msg.content == empty_content
    assert msg.payload == empty_payload
    assert msg.metadata == empty_metadata
