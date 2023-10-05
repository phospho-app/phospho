"""
Define the message class
"""

class Message:
    # Typed attributes
    def __init__(self, content: str, payload: dict={}, metadata: dict={}):
        self.content = content # can be empty, even though it doesn't make sense. Cannot be None
        self.payload = payload # Implemented by the dev user, can be empty
        self.metadata = metadata # timestamp, user_id, etc. TODO: define the metadata

    def __str__(self):
        message = {}
        message["content"] = self.content
        message["payload"] = self.payload
        message["metadata"] = self.metadata
        return str(message)