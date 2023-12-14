from .agent import Agent
from .message import Message
from .client import Client
from .consumer import Consumer
from .log_queue import LogQueue, Event
from .utils import (
    generate_timestamp,
    generate_uuid,
    convert_to_jsonable_dict,
    is_jsonable,
    MutableAsyncGenerator,
    MutableGenerator,
)
from .extractor import get_input_output, RawDataType
from ._version import __version__
from . import evals

__all__ = [
    "Client",
    "Consumer",
    "LogQueue",
    "Event",
    "generate_timestamp",
    "generate_uuid",
    "convert_to_jsonable_dict",
    "get_input_output",
    "RawDataType",
    "MutableAsyncGenerator",
    "MutableGenerator",
    "client",
    "log_queue",
    "consumer",
    "current_session_id",
    "new_session",
    "log",
    "wrap",
    "extractor",
    "evals",
]

import pydantic
import logging

from copy import deepcopy
from typing import (
    Dict,
    Any,
    Optional,
    Union,
    Callable,
    Tuple,
    Iterable,
    AsyncIterable,
    Coroutine,
    Generator,
    AsyncGenerator,
)


client = None
log_queue = None
consumer = None

logger = logging.getLogger(__name__)


def init(
    api_key: Optional[str] = None,
    project_id: Optional[str] = None,
    tick: float = 0.5,
) -> None:
    """
    Initialize the phospho logging module.

    This sets up a log_queue, stored in memory, and a consumer. Calls to `phospho.log()`
    push logs content to the log_queue. Every tick, the consumer tries to push the content
    of the log_queue to the phospho backend.

    :param api_key: Phospho API key
    :param project_id: Phospho project id
    :param verbose: whether to display logs
    :param tick: how frequently the consumer tries to push logs to the backend (in seconds)
    """
    global client
    global log_queue
    global consumer

    client = Client(api_key=api_key, project_id=project_id)
    log_queue = LogQueue()
    consumer = Consumer(log_queue=log_queue, client=client, tick=tick)
    # Start the consumer on a separate thread (this will periodically send logs to backend)
    consumer.start()


def new_session() -> str:
    """
    Sessions are used to group tasks and logs together.

    Use `phospho.new_session()` when you start a new conversation. Store the returned
    `session_id` and pass it to `phospho.log` to group logs together.

    ```
    session_id = phospho.new_session()
    my_database.store(session_id)
    phospho.log(input="stuff", session_id=session_id)
    ```

    :returns: The generated session_id.
    """
    global current_session_id
    current_session_id = generate_uuid()
    return current_session_id


def _log_single_event(
    input: Union[RawDataType, str],
    output: Optional[Union[RawDataType, str]] = None,
    session_id: Optional[str] = None,
    task_id: Optional[str] = None,
    raw_input: Optional[RawDataType] = None,
    raw_output: Optional[RawDataType] = None,
    input_to_str_function: Optional[Callable[[Any], str]] = None,
    output_to_str_function: Optional[Callable[[Any], str]] = None,
    concatenate_raw_outputs_if_task_id_exists: bool = True,
    to_log: bool = True,
    **kwargs: Dict[str, Any],
) -> Dict[str, object]:
    """Log a single event.

    Internal function used to push stuff to log_queue and mark them as to be sent
    to the logging endpoint or not.
    """
    global client
    global log_queue
    global current_session_id

    assert (
        (log_queue is not None) and (client is not None)
    ), "phospho.log() was called but the global variable log_queue was not found. Make sure that phospho.init() was called."

    # Process the input and output to convert them to dict
    (
        input_to_log,
        output_to_log,
        raw_input_to_log,
        raw_output_to_log,
        task_id_from_output,
        extracted_to_log,
    ) = get_input_output(
        input=input,
        output=output,
        raw_input=raw_input,
        raw_output=raw_output,
        input_to_str_function=input_to_str_function,
        output_to_str_function=output_to_str_function,
    )

    # Override to_log parameter
    if extracted_to_log is not None:
        to_log = extracted_to_log

    # Task: use the task_id parameter, the task_id infered from inputs, or generate one
    if task_id is None:
        if task_id_from_output is None:
            # if nothing specified, create new id.
            task_id = generate_uuid()
        else:
            task_id = task_id_from_output

    # Every other kwargs will be directly stored in the logs, if it's json serializable
    if kwargs:
        kwargs_to_log = convert_to_jsonable_dict(kwargs)
    else:
        kwargs_to_log = {}

    # The log event looks like this:
    log_content: Dict[str, object] = {
        "client_created_at": generate_timestamp(),
        # metadata
        "project_id": client._project_id(),
        "session_id": session_id,  # Note: can be None
        "task_id": task_id,
        # input
        "input": str(input_to_log),
        "raw_input": raw_input_to_log,
        "raw_input_type_name": type(input).__name__,
        # output
        "output": output_to_log,
        "raw_output": raw_output_to_log,
        "raw_output_type_name": type(output).__name__,
        # other
        **kwargs_to_log,
    }

    logger.debug(f"Existing task_id: {list(log_queue.events.keys())}")
    logger.debug(f"Current task_id: {task_id}")

    if task_id in log_queue.events.keys():
        # If the task_id already exists in log_queue, update the existing event content
        # Update the dict inplace
        existing_log_content = log_queue.events[task_id].content

        # Concatenate the log event output strings, unless if everything is None
        if existing_log_content["output"] is None and log_content["output"] is None:
            fused_output = None
        else:
            if existing_log_content["output"] is None:
                existing_log_content["output"] = ""
            if log_content["output"] is None:
                log_content["output"] = ""
            fused_output = str(existing_log_content["output"]) + str(
                log_content["output"]
            )

        fused_log_content = {
            # Replace creation timestamp by the original one
            # Keep a trace of the latest timestamp. This will help computing streaming time
            "client_created_at": existing_log_content["client_created_at"],
            "last_update": log_content["client_created_at"],
            # Concatenate the log event output strings
            "output": fused_output,
            "raw_output": [
                existing_log_content["raw_output"],
                log_content["raw_output"],
            ]
            if not isinstance(existing_log_content["raw_output"], list)
            else existing_log_content["raw_output"] + [log_content["raw_output"]],
        }
        # TODO : Turn this bool into a parametrizable list
        if concatenate_raw_outputs_if_task_id_exists:
            log_content.pop("raw_output")
        existing_log_content.update(log_content)
        existing_log_content.update(fused_log_content)
        # Concatenate the raw_outputs to keep all the intermediate results to openai
        if concatenate_raw_outputs_if_task_id_exists:
            if isinstance(existing_log_content["raw_output"], list):
                existing_log_content["raw_output"].append(raw_output_to_log)
            else:
                existing_log_content["raw_output"] = [
                    existing_log_content["raw_output"],
                    raw_output_to_log,
                ]
        log_content = existing_log_content
        # Update the to_log status of event
        log_queue.events[task_id].to_log = to_log
    else:
        # Append event to log_queue
        log_queue.append(event=Event(id=task_id, content=log_content, to_log=to_log))

    # logger.debug("Updated dict:" + str(log_queue.events[task_id].content))
    # logger.debug("To log" + str(log_queue.events[task_id].to_log))

    return log_content


def _wrap_iterable(
    output: Union[Iterable[RawDataType], AsyncIterable[RawDataType]]
) -> None:
    """Wrap the class of a passed output so that it nows log its generated
    content to phospho.

    This mutate the class inplace and adds the attribute _phospho_wrapped
    to avoid wrapping it again.

    Logging will only be performed on instances that have the attribute
    _phospho_metadata.
    """
    global log_queue

    # Wrap the class iterator with a phospho logging callback
    if not hasattr(output.__class__, "_phospho_wrapped") or (
        output.__class__._phospho_wrapped is False
    ):
        # Create a copy of the iterator function
        # Q: Do this with __iter__ as well ?
        if isinstance(output, Iterable):
            class_next_func_copy = deepcopy(output.__next__.__func__)

            def wrapped_next(self):
                """At every iteration step, phospho stores the intermediate value internally
                if asked to do so for this instance."""
                try:
                    value = class_next_func_copy(self)
                    # Only log instances that have the _phosphometadata attribute (set when
                    # passed to phospho.log)
                    if hasattr(self, "_phospho_metadata"):
                        _log_single_event(
                            output=value, to_log=False, **self._phospho_metadata
                        )
                    return value
                except StopIteration:
                    if hasattr(self, "_phospho_metadata"):
                        _log_single_event(
                            output=None, to_log=True, **self._phospho_metadata
                        )
                    raise StopIteration

            def wrapped_iter(self):
                """The phospho wrapper flushes the log at the end of the iteration
                if asked to do so for this instance."""
                while True:
                    try:
                        yield self.__next__()
                    except StopIteration:
                        # Iteration finished, push the logs
                        break

            # Update the class iterators to be wrapped
            output.__class__.__next__ = wrapped_next
            output.__class__.__iter__ = wrapped_iter
            # Mark the class as wrapped to avoid wrapping it multiple time
            output.__class__._phospho_wrapped = True

        elif isinstance(output, AsyncIterable):
            class_anext_func_copy = deepcopy(output.__anext__.__func__)

            async def wrapped_anext(self):
                """At every iteration step, phospho stores the intermediate value internally
                if asked to do so for this instance."""
                try:
                    value = await class_anext_func_copy(self)
                    # Only log instances that have the _phosphometadata attribute (set when
                    # passed to phospho.log)
                    if hasattr(self, "_phospho_metadata"):
                        _log_single_event(
                            output=value, to_log=False, **self._phospho_metadata
                        )
                    return value
                except StopAsyncIteration:
                    if hasattr(self, "_phospho_metadata"):
                        _log_single_event(
                            output=None, to_log=True, **self._phospho_metadata
                        )
                    raise StopAsyncIteration

            async def wrapped_aiter(self):
                """The phospho wrapper flushes the log at the end of the iteration
                if asked to do so for this instance."""
                while True:
                    try:
                        yield await self.__anext__()
                    except StopAsyncIteration:
                        # Iteration finished, push the logs
                        break

            # Update the class iterators to be wrapped
            output.__class__.__anext__ = wrapped_anext
            # output.__class__.__aiter__ = wrapped_aiter

        else:
            raise NotImplementedError(
                f"Unsupported output type for wrapping iterable: {type(output)}"
            )

        # Mark the class as wrapped to avoid wrapping it multiple time
        output.__class__._phospho_wrapped = True


def log(
    input: Union[RawDataType, str],
    output: Optional[Union[RawDataType, str, Iterable[RawDataType]]] = None,
    session_id: Optional[str] = None,
    task_id: Optional[str] = None,
    raw_input: Optional[RawDataType] = None,
    raw_output: Optional[RawDataType] = None,
    # todo: group those into "transformation"
    input_to_str_function: Optional[Callable[[Any], str]] = None,
    output_to_str_function: Optional[Callable[[Any], str]] = None,
    output_to_task_id_and_to_log_function: Optional[
        Callable[[Any], Tuple[Optional[str], bool]]
    ] = None,
    concatenate_raw_outputs_if_task_id_exists: bool = True,
    stream: bool = False,
    **kwargs: Dict[str, Any],
) -> Dict[str, object]:
    """Phospho's main all-purpose logging endpoint, with support for streaming.

    Usage:
    ```
    phospho.log(input="input", output="output")
    ```

    By default, phospho will try to interpret a string representation from `input` and `output`.
    For example, OpenAI API calls. Arguments passed as `input` and `output` are then stored
    in `raw_input` and `raw_output`, unless those are specified.

    You can customize this behaviour using `input_to_str_function` and `output_to_str_function`.

    `session_id` is used to group logs together. For example, a single conversation.

    By default, every log is assigned to a unique `task_id` and is immediately pushed to backend.
    However, if you pass multiple logs with the same `task_id` and `to_log=False`, they will
    stay in queue until they receive the same `task_id` with `to_log=False`. They will then
    be combined and pushed to backend.
    You can automate this behaviour using `output_to_task_id_and_to_log_function`. This is used
    to handle streaming.

    Every other `**kwargs` will be added to the log content and stored.

    :returns:
    - log_event (Dict[str, object]):
        The content of what has been logged.
    """
    if stream:
        # Implement the streaming logic over the output
        # Note: The output must be mutable. Generators are not mutable
        mutable_error = """phospho.log was called with stream=True, which requires output to be mutable. 
However, output type {output} is immutable because it's an instance of {instance},
Wrap this generator into a mutable object for phospho.log to work:
"""
        if isinstance(output, AsyncGenerator):
            raise ValueError(
                mutable_error.format(output=type(output), instance="AsyncGenerator")
                + """
mutable_output = phospho.MutableAsyncGenerator(generator)
phospho.log(input=input, output=mutable_output, stream=True)\n
"""
            )
        elif isinstance(output, Generator):
            raise ValueError(
                mutable_error.format(output=type(output), instance="Generator")
                + """
mutable_output = phospho.MutableGenerator(generator)
phospho.log(input=input, output=mutable_output, stream=True)\n
"""
            )

        # Verify that output is iterable
        if isinstance(output, AsyncIterable) or isinstance(output, Iterable):
            _wrap_iterable(output)
            # Modify the instance inplace to carry additional metadata
            task_id = generate_uuid()
            output._phospho_metadata = {
                "input": input,
                # do not put output in the metadata, as it will change with __next__
                "session_id": session_id,
                "task_id": task_id,  # Mark these with the same, custom task_id
                "raw_input": raw_input,
                "raw_output": raw_output,
                "input_to_str_function": input_to_str_function,
                "output_to_str_function": output_to_str_function,
                "output_to_task_id_and_to_log_function": output_to_task_id_and_to_log_function,
                "concatenate_raw_outputs_if_task_id_exists": concatenate_raw_outputs_if_task_id_exists,
            }
            # Return the log:
            log = {"output": None, **output._phospho_metadata}
            # log = _log_single_event(**log, to_log=False)
            return log
        else:
            logger.warning(
                f"phospho.log was called with stream=True but output type {type(output)} is not supported. Trying to log with stream=False."
            )
    else:
        # If stream=False, push directly the log to log_queue
        # TODO : Make type validation cleaner
        assert (
            (output is None)
            or isinstance(output, str)
            or isinstance(output, pydantic.BaseModel)
            or is_jsonable(output)
        ), f"If stream=False, you can't log output type {type(output)}. If you want to log a stream, pass stream=True to phospho.log"

    log = _log_single_event(
        input=input,
        output=output,
        session_id=session_id,
        task_id=task_id,
        raw_input=raw_input,
        raw_output=raw_output,
        input_to_str_function=input_to_str_function,
        output_to_str_function=output_to_str_function,
        output_to_task_id_and_to_log_function=output_to_task_id_and_to_log_function,
        concatenate_raw_outputs_if_task_id_exists=concatenate_raw_outputs_if_task_id_exists,
        to_log=True,
        **kwargs,
    )

    return log


def _wrap(
    __fn,
    stream: bool = False,
    stop: Optional[Callable[[Any], bool]] = None,
    **meta_wrap_kwargs: Any,
) -> Callable[[Any], Any]:
    """
    Internal wrapper
    """
    # Stop is the stopping criterion for streaming mode
    if stop is None:
        # Default behaviour = stop when None is returned
        stop = lambda x: x is None

    def streamed_function_wrapper(
        func_args: Iterable[Any],
        func_kwargs: Dict[str, Any],
        output: Any,
        task_id: str,
    ):
        # This function is used so that the wrapped_function can
        # return a generator that also logs.
        # Group the kwargs with the function kwargs
        _meta_wrap_kwargs = {**meta_wrap_kwargs, **func_kwargs}

        for single_output in output:
            if not stop(single_output):
                _log_single_event(
                    input={
                        **{str(i): arg for i, arg in enumerate(func_args)},
                        **func_kwargs,
                    },
                    output=single_output,
                    # Group the generated outputs with a unique task_id
                    task_id=task_id,
                    # By default, individual streamed calls are not immediately logged
                    to_log=False,
                    **_meta_wrap_kwargs,
                )
            else:
                _log_single_event(
                    input={
                        **{str(i): arg for i, arg in enumerate(func_args)},
                        **func_kwargs,
                    },
                    output=None,
                    task_id=task_id,
                    to_log=True,
                    **_meta_wrap_kwargs,
                )
            yield single_output

    async def async_streamed_function_wrapper(
        func_args: Iterable[Any],
        func_kwargs: Dict[str, Any],
        output: Coroutine,
        task_id: str,
    ):
        # This function is used so that the wrapped_function can
        # return a generator that also logs.
        _meta_wrap_kwargs = {**meta_wrap_kwargs, **func_kwargs}

        async for single_output in await output:
            if not stop(single_output):
                _log_single_event(
                    input={
                        **{str(i): arg for i, arg in enumerate(func_args)},
                        **func_kwargs,
                    },
                    output=single_output,
                    # Group the generated outputs with a unique task_id
                    task_id=task_id,
                    # By default, individual streamed calls are not immediately logged
                    to_log=False,
                    **_meta_wrap_kwargs,
                )
            else:
                _log_single_event(
                    input={
                        **{str(i): arg for i, arg in enumerate(func_args)},
                        **func_kwargs,
                    },
                    output=None,
                    task_id=task_id,
                    to_log=True,
                    **_meta_wrap_kwargs,
                )
            yield single_output

    def wrapped_function(*func_args, **func_kwargs):
        # Call the wrapped function
        logging.debug("Wrapping function" + str(__fn))
        output = __fn(*func_args, **func_kwargs)

        _meta_wrap_kwargs = {**meta_wrap_kwargs, **func_kwargs}

        # Log
        # If not stream, but stream=True passed to the wrapped function, then have the streaming behaviour
        if not stream and (func_kwargs.get("stream", False) is False):
            # Default behaviour (not streaming): log the input and the output
            _log_single_event(
                # Input is all the args and kwargs passed to the funciton
                input={
                    **{str(i): arg for i, arg in enumerate(func_args)},
                    **func_kwargs,
                },
                # Output is what the function returns
                output=output,
                # Also log everything passed to the wrapper
                **_meta_wrap_kwargs,
            )
            return output
        else:
            # Streaming behaviour
            # Return a generator that log every individual streamed output
            task_id = generate_uuid()
            logging.debug("Wrapping function with stream=True" + str(output))
            if isinstance(output, Coroutine):
                return async_streamed_function_wrapper(
                    func_args=func_args,
                    func_kwargs=func_kwargs,
                    output=output,
                    task_id=task_id,
                )
            else:
                return streamed_function_wrapper(
                    func_args=func_args,
                    func_kwargs=func_kwargs,
                    output=output,
                    task_id=task_id,
                )

    return wrapped_function


def wrap(
    __fn: Optional[Callable[[Any], Any]] = None,
    *,
    stream: bool = False,
    stop: Optional[Callable[[Any], bool]] = None,
    **meta_kwargs,
):
    """
    This wrapper helps you log a function call to phospho by returning a wrapped version
    of the function.

    The wrapped function calls `phospho.log` and sets `input` to be the function's arguments,
    and the `output` to be the returned value.

    Additional arguments to `phospho.wrap` will also be logged. Example:

    ```python
    response = phospho.wrap(
        # Wrap the call to this function
        openai_client.chat.completions.create,
        # Specify more metadata to be logged
        metadata={"more": "details"},
    )(
        # Call your function as usual
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello!"}]
    )
    # Just as before, response is a `openai.types.chat.chat_completion.ChatCompletion` object.
    # You can display the generated message this way:
    print(response.choices[0].message.content)
    ```

    Console output:
    ```text
    Hello! How can I assist you today?
    ```

    ### Streaming

    If the parameter `stream=True` is passed to the wrapped function, then the wrapped function returns
    a generator that iterates over the function output, and logs every individual output. Example:

    ```
    response = phospho.wrap(
        openai_client.chat.completions.create
    )(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": "Hello!"}],
        # Pass the stream=True parameter, as usual with openai
        stream=True,
    )
    full_text_response = ""
    for r in response:
        # Every `r` is a `openai.types.chat.chat_completion_chunk.ChatCompletionChunk` object
        full_text_response += partial_response r.choices[0].delta.content

    print(full_text_response)
    ```

    Console output:
    ```text
    Hello! How can I assist you today?
    ```

    Passing `stream=False` or `stream=None` disable the behaviour.

    ### Non-keyword arguments

    Passing a non-keyword argument will log it in phospho with a integer id. Example:

    `phospho.wrap(some_function)("some_value", "another_value")`

    Will be logged as `{"0": "some_value", "1": "another_value"}`

    Use keyword arguments to

    :returns: The wrapped function with additional logging.
    """

    def meta_wrapper(func, *args, **kwargs):
        # Merge the meta_args and meta_kwargs passed to phospho.wrap
        # with the args and kwargs passed to the wrapped function
        # and pass them to the wrapper
        _meta_kwargs = {**meta_kwargs, **kwargs}

        return _wrap(func, *args, stream=stream, stop=stop, **_meta_kwargs)

    if __fn is None:
        return meta_wrapper
    else:
        return meta_wrapper(__fn)
