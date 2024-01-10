import time
import json
import uuid
import logging
import pydantic

from typing import Any, Dict, AsyncGenerator, Generator, Callable, Union

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


def filter_nonjsonable_keys(arg_dict: dict, verbose: bool = False) -> Dict[str, object]:
    if not isinstance(arg_dict, dict):
        raise TypeError(f"Expected a dict, got {type(arg_dict)}")

    if verbose:
        original_keys = set(arg_dict.keys())
    # Filter the keys to only keep the ones that json serializable
    new_arg_dict = {key: value for key, value in arg_dict.items() if is_jsonable(value)}
    if verbose:
        new_keys = set(new_arg_dict.keys())
        dropped_keys = original_keys - new_keys
        if dropped_keys:
            logger.warning(
                f"Logging skipped for the keys that aren't json serializable (no .toJSON() method): {', '.join(dropped_keys)}"
            )
    return new_arg_dict


def convert_content_to_loggable_content(
    content: Any
) -> Union[Dict[str, object], str, None]:
    """
    Convert objects to json serializable content. Notably, nested dicts and lists are converted.
    """
    if is_jsonable(content):
        return content

    if isinstance(content, dict):
        new_content = {
            key: convert_content_to_loggable_content(value)
            for key, value in content.items()
        }
        return new_content
    elif isinstance(content, list):
        # Special case for list
        return str([convert_content_to_loggable_content(x) for x in content])
    elif isinstance(content, pydantic.BaseModel):
        return content.model_dump()
    elif isinstance(content, pydantic.v1.BaseModel):
        return content.dict()
    elif isinstance(content, bytes):
        # Probably a byte representation of json
        return json.loads(content.decode())
    else:
        # Fallback to str
        logger.debug(
            f"Unknwon type {type(content)} for content {content}. Fallback to str."
        )
        return str(content)


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
