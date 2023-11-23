import time
import json
import uuid

from typing import Any


def generate_timestamp() -> int:
    """Returns the current UNIX timestamp in seconds"""
    return int(time.time())


def generate_uuid() -> str:
    return uuid.uuid4().hex


def is_jsonable(x: Any) -> bool:
    try:
        json.dumps(x)
        return True
    except TypeError:
        return False


def filter_nonjsonable_keys(arg_dict: dict) -> dict:
    """Return a copy of arg_dict only with jsonable key:value items (greedy)"""
    return {key: value for key, value in arg_dict.items() if is_jsonable(value)}
