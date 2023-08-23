"""
Define the message class
"""
import threading # Forensuring thread safety



class Message:
    # Typed attributes
    def __init__(self, content: str, payload: dict, metadata: dict):
        self.content = content # can be empty, even though it doesn't make sense
        self.payload = payload # Implemented by the dev user, can be empty
        self.metadata = metadata # timestamp, user_id, etc. TODO: define the metadata