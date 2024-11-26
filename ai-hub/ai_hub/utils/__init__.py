import time
import uuid


def generate_timestamp() -> int:
    """
    Returns the current UNIX timestamp in seconds
    """
    return int(time.time())


def generate_uuid(prefix: str = "") -> str:
    """
    Add a prefiw if needed to the uuid
    Example: generate_uuid("file_") to have a file_id
    """
    value = uuid.uuid4().hex
    return f"{prefix}{value}"
