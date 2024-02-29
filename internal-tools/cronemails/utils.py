import time


def generate_timestamp() -> int:
    """
    Returns the current UNIX timestamp in seconds
    """
    return int(time.time())
