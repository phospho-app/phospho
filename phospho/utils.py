import time
import json
import uuid
import logging

from typing import Any, Dict

logger = logging.getLogger(__name__)


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


def convert_to_jsonable_dict(
    arg_dict: dict, verbose: bool = False
) -> Dict[str, object]:
    if verbose:
        original_keys = set(arg_dict.keys())
    # Filter the keys to only keep the ones that json serializable
    new_arg_dict = filter_nonjsonable_keys(arg_dict)
    if verbose:
        new_keys = set(new_arg_dict.keys())
        dropped_keys = original_keys - new_keys
        if dropped_keys:
            logger.warning(
                f"Logging skipped for the keys that aren't json serializable (no .toJSON() method): {', '.join(dropped_keys)}"
            )
    return new_arg_dict
