"""
Define the message class
"""
from typing import Optional


class Message:
    # Typed attributes
    def __init__(
        self,
        content: str,
        payload: Optional[dict] = None,
        metadata: Optional[dict] = None,
    ):
        # Can be empty, even though it doesn't make sense. Cannot be None
        self.content = content
        # Implemented by the dev user, can be empty
        if payload is not None:
            self.payload = payload
        else:
            payload = {}
        # timestamp, user_id, etc. TODO: define the metadata
        if metadata is not None:
            self.metadata = metadata
        else:
            self.metadata = {}

    def __str__(self):
        message = {}
        message["content"] = self.content
        message["payload"] = self.payload
        message["metadata"] = self.metadata
        return str(message)
