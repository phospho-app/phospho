import time
import json
import uuid
import logging

from typing import Any, Dict, AsyncGenerator, Generator, Callable

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


class MutableGenerator:
    def __init__(self, generator: Generator, stop: Callable[[Any], bool]):
        """Transform a generator into a mutable object that can be logged.

        generator (Generator):
            The generator to be wrapped
        stop (Callable[[Any], bool])):
            Stopping criterion for generation. If stop(generated_value) is True,
            then we stop the generation.
        """
        self.generator = generator
        self.stop = stop

    def __iter__(self):
        return self

    def __next__(self):
        value = self.generator.__next__()
        if self.stop(value):
            raise StopIteration
        return value


class MutableAsyncGenerator:
    def __init__(self, generator: AsyncGenerator, stop: Callable[[Any], bool]):
        """Transform an async generator into a mutable object that can be logged.

        generator (AsyncGenerator):
            The generator to be wrapped
        stop (Callable[[Any], bool])):
            Stopping criterion for generation. If stop(generated_value) is True,
            then we stop the generation.
        """
        self.generator = generator
        self.stop = stop

    def __aiter__(self):
        return self

    async def __anext__(self):
        value = await self.generator.__anext__()
        if self.stop(value):
            raise StopAsyncIteration
        return value
