import time
import uuid


def generate_timestamp() -> int:
    """Returns the current UNIX timestamp in seconds"""
    return int(time.time())


def generate_uuid() -> str:
    return uuid.uuid4().hex
