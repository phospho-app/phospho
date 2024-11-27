import datetime
import re
import time
import uuid
from collections import Counter
from typing import Tuple

import tiktoken


def generate_uuid() -> str:
    return uuid.uuid4().hex


def generate_timestamp() -> int:
    """
    Returns the current UNIX timestamp in seconds
    """
    return int(time.time())


def get_most_common(items):
    if not items:
        return None
    return Counter(items).most_common(1)[0][0]


def validate_project_name(project_name: str) -> bool:
    """
    (Deprecated)
    Currently not used in the backend.
    """
    # Must start with a letter or number
    if not re.match("^[a-z]", project_name):
        return False

    # Check that the project name respects the naming convention
    if not re.match("^[a-z0-9-]*$", project_name):
        return False
    else:
        return True


def fits_in_context_window(prompt: str, context_window_size: int) -> bool:
    """
    Check if the prompt fits in the context window
    context_window_size is the number of tokens of the context window
    """
    encoding = tiktoken.get_encoding("cl100k_base")

    num_tokens = len(encoding.encode(prompt))

    return num_tokens <= context_window_size


def get_last_week_timestamps() -> Tuple[int, int]:
    """
    Returns the UNIX timestamps of the beginning of the day 7 days ago and today
    """

    # Get the last week's timestamp
    today_datetime = datetime.datetime.now(datetime.timezone.utc)
    today_timestamp = int(today_datetime.timestamp())
    seven_days_ago_datetime = today_datetime - datetime.timedelta(days=6)
    # Round to the beginning of the day
    seven_days_ago_datetime = seven_days_ago_datetime.replace(
        hour=0, minute=0, second=0, microsecond=0
    )
    seven_days_ago_timestamp = int(seven_days_ago_datetime.timestamp())
    return seven_days_ago_timestamp, today_timestamp
