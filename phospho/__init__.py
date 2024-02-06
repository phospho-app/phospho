from .agent import Agent
from .message import Message
from .client import Client
from .consumer import Consumer
from .log_queue import LogQueue, Event
from .tasks import Task
from .utils import (
    generate_timestamp,
    generate_uuid,
    filter_nonjsonable_keys,
    is_jsonable,
    MutableAsyncGenerator,
    MutableGenerator,
    convert_content_to_loggable_content,
)
from .extractor import (
    extract_data_from_input,
    extract_data_from_output,
    extract_metadata_from_input_output,
    RawDataType,
)
from ._version import __version__
from . import config, integrations, models
from .testing import PhosphoTest

__all__ = [
    "Client",
    "Consumer",
    "LogQueue",
    "Event",
    "generate_timestamp",
    "generate_uuid",
    "filter_nonjsonable_keys",
    "is_jsonable",
    "__version__",
    "extract_data_from_input_output",
    "RawDataType",
    "MutableAsyncGenerator",
    "MutableGenerator",
    "client",
    "log_queue",
    "consumer",
    "latest_task_id",
    "latest_session_id",
    "new_session",
    "log",
    "wrap",
    "extractor",
    "PhosphoTest",
    "config",
    "integrations",
]

import logging
import pydantic

from copy import deepcopy
from typing import (
    Dict,
    Any,
    Literal,
    Optional,
    Union,
    Callable,
    Iterable,
    AsyncIterable,
    Coroutine,
    Generator,
    AsyncGenerator,
)


client = None
log_queue = None
consumer = None
latest_task_id = None
latest_session_id = None

logger = logging.getLogger(__name__)


def init(
    api_key: Optional[str] = None,
    project_id: Optional[str] = None,
    base_url: Optional[str] = None,
    tick: float = 0.5,
    raise_error_on_fail_to_send: bool = False,
) -> None:
    """
    Initialize the phospho logging module.

    This sets up a log_queue, stored in memory, and a consumer. Calls to `phospho.log()`
    push logs content to the log_queue. Every tick, the consumer tries to push the content
    of the log_queue to the phospho backend.

    :param api_key: Phospho API key
    :param project_id: Phospho project id
    :param base_url: URL to the phospho backend
    :param verbose: whether to display logs
    :param tick: how frequently the consumer tries to push logs to the backend (in seconds)
    """
    global client
    global log_queue
    global consumer

    client = Client(api_key=api_key, project_id=project_id, base_url=base_url)
    log_queue = LogQueue()
    consumer = Consumer(
        log_queue=log_queue,
        client=client,
        tick=tick,
        raise_error_on_fail_to_send=raise_error_on_fail_to_send,
    )
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
    global latest_session_id
    latest_session_id = generate_uuid()
    return latest_session_id


def new_task() -> str:
    """
    Tasks are the main unit of logging in phospho.

    Use `phospho.new_task()` when you start a new, complex task. Store the returned
    `task_id` and pass it to `phospho.log` to group logs together.

    :returns: The generated task_id.
    """
    global latest_task_id
    latest_task_id = generate_uuid()
    return latest_task_id


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
    input_output_to_usage_function: Optional[
        Callable[[Any, Any], Dict[str, float]]
    ] = None,
    to_log: bool = True,
    **kwargs: Any,
) -> Dict[str, object]:
    """Log a single event.

    Internal function used to push stuff to log_queue and mark them as to be sent
    to the logging endpoint or not.
    """
    global client
    global log_queue
    global latest_task_id
    global latest_session_id

    input = convert_content_to_loggable_content(input)
    output = convert_content_to_loggable_content(output)
    raw_input = convert_content_to_loggable_content(raw_input)
    raw_output = convert_content_to_loggable_content(raw_output)
    kwargs = convert_content_to_loggable_content(kwargs)

    assert (
        (log_queue is not None) and (client is not None)
    ), "phospho.log() was called but the global variable log_queue was not found. Make sure that phospho.init() was called."

    # Process the input and output to convert them to dict
    (
        input_to_log,
        raw_input_to_log,
    ) = extract_data_from_input(
        input=input,
        raw_input=raw_input,
        input_to_str_function=input_to_str_function,
    )
    (
        output_to_log,
        raw_output_to_log,
    ) = extract_data_from_output(
        output=output,
        raw_output=raw_output,
        output_to_str_function=output_to_str_function,
    )
    metadata_to_log = extract_metadata_from_input_output(
        input=input,
        output=output,
        input_output_to_usage_function=input_output_to_usage_function,
    )

    # Task: use the task_id parameter, the task_id infered from inputs, or generate one
    if task_id is None:
        task_id = generate_uuid()

    # Keep track of the latest task_id and session_id
    latest_task_id = task_id
    latest_session_id = session_id

    # Every other kwargs will be directly stored in the logs, if it's json serializable
    if kwargs:
        kwargs_to_log = filter_nonjsonable_keys(kwargs)
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
        "input": input_to_log,
        "raw_input": raw_input_to_log,
        "raw_input_type_name": type(input).__name__,
        # output
        "output": output_to_log,
        "raw_output": raw_output_to_log,
        "raw_output_type_name": type(output).__name__,
        # other
        **metadata_to_log,
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
        # Concatenate the raw_outputs to keep all the intermediate results to openai
        if (
            existing_log_content["raw_output"] is None
            and log_content["raw_output"] is None
        ):
            fused_raw_output = None
        else:
            if existing_log_content["raw_output"] is None:
                existing_log_content["raw_output"] = []
            if log_content["raw_output"] is None:
                log_content["raw_output"] = []
            # Convert to list if not already
            if not isinstance(existing_log_content["raw_output"], list):
                existing_log_content["raw_output"] = [
                    existing_log_content["raw_output"]
                ]
            if not isinstance(log_content["raw_output"], list):
                log_content["raw_output"] = [log_content["raw_output"]]
            fused_raw_output = (
                existing_log_content["raw_output"] + log_content["raw_output"]
            )
        # For usage metrics in metadata, apply heuristics
        fused_completion_tokens: Optional[int] = None
        if "completion_tokens" in log_content:
            fused_completion_tokens = log_content["completion_tokens"]
            fused_completion_tokens += existing_log_content.get("completion_tokens", 0)
        fused_total_tokens: Optional[int] = None
        if "total_tokens" in log_content:
            fused_total_tokens = log_content["total_tokens"]
            fused_total_tokens += existing_log_content.get("total_tokens", 0)

        # Put all of this into a dict
        fused_log_content = {
            # Replace creation timestamp by the original one
            # Keep a trace of the latest timestamp. This will help computing streaming time
            "client_created_at": existing_log_content["client_created_at"],
            "last_update": log_content["client_created_at"],
            # Concatenate the log event output strings
            "output": fused_output,
            "raw_output": fused_raw_output,
        }
        if fused_completion_tokens is not None:
            fused_log_content["completion_tokens"] = fused_completion_tokens
        if fused_total_tokens is not None:
            fused_log_content["total_tokens"] = fused_total_tokens
        # TODO : Turn this bool into a parametrizable list
        if concatenate_raw_outputs_if_task_id_exists:
            log_content.pop("raw_output")
        existing_log_content.update(log_content)
        # Update the dict inplace
        existing_log_content.update(fused_log_content)
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
    version_id: Optional[str] = None,
    user_id: Optional[str] = None,
    raw_input: Optional[RawDataType] = None,
    raw_output: Optional[RawDataType] = None,
    # todo: group those into "transformation"
    input_to_str_function: Optional[Callable[[Any], str]] = None,
    output_to_str_function: Optional[Callable[[Any], str]] = None,
    concatenate_raw_outputs_if_task_id_exists: bool = True,
    input_output_to_usage_function: Optional[Callable[[Any], Dict[str, float]]] = None,
    stream: bool = False,
    **kwargs: Dict[str, Any],
) -> Optional[Dict[str, object]]:
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

    `task_id` is used to identify a single task. For example, a single message in a conversation.
    This is useful to log user feedback on a specific task (see phospho.user_feedback).

    `version_id` is used for A/B testing. It is a string that identifies the version of the
    code that generated the log. For example, "v1.0.0" or "test".

    `user_id` is used to identify the user. For example, a user's email.

    `input_output_to_usage_function` is used to count the number of tokens in prompt and in completion.
    It takes (input, output) as a value and returns a dict with keys `prompt_tokens`, `completion_tokens`,
    `total_tokens`.

    `stream` is used to log a stream of data. For example, a generator. If `stream=True`, then
    `phospho.log` returns a generator that also logs every individual output. See `phospho.wrap`
    for more details.

    Every other `**kwargs` will be added to the metadata and stored.

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
                "user_id": user_id,
                "version_id": version_id,
                "raw_input": raw_input,
                "raw_output": raw_output,
                "input_to_str_function": input_to_str_function,
                "output_to_str_function": output_to_str_function,
                "input_output_to_usage_function": input_output_to_usage_function,
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

        assert not isinstance(output, AsyncIterable) or not isinstance(
            output, Iterable
        ), (
            "Phospho can't log output type {type(output)} with stream=False. To log a stream, pass stream=True."
            + " To log a complex object, pass a pydantic.BaseModel or a json serializable object."
        )

    log = _log_single_event(
        input=input,
        output=output,
        session_id=session_id,
        task_id=task_id,
        user_id=user_id,
        version_id=version_id,
        raw_input=raw_input,
        raw_output=raw_output,
        input_to_str_function=input_to_str_function,
        output_to_str_function=output_to_str_function,
        input_output_to_usage_function=input_output_to_usage_function,
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

        def default_stop_function(x: Any) -> bool:
            if x is None:
                return True
            if isinstance(x, dict):
                choices = x.get("choices", [])
                if len(choices) > 0:
                    if choices[0].get("finish_reason", None) is not None:
                        return True
                    if choices[0].get("delta", {}).get("content", None) is None:
                        return True
            if isinstance(x, pydantic.BaseModel):
                try:
                    finish_reason = x.choices[0].finish_reason
                    if finish_reason is not None:
                        return True
                except Exception as e:
                    pass
            return False

        stop = default_stop_function

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


def user_feedback(
    task_id: str,
    flag: Optional[Literal["success", "failure"]] = None,
    notes: Optional[str] = None,
    source: str = "user",
    raw_flag: Optional[str] = None,
    raw_flag_to_flag: Optional[Callable[[Any], Literal["success", "failure"]]] = None,
) -> Task:
    """
    Flag a task already logged to phospho as a `success` or a `failure`. This is useful to collect human feedback.

    Note: Feedback can be directly logged with `phospho.log` by passing `flag` as a keyword argument.

    :param task_id: The task_id of the task to flag. Get the task_id from the returned value of phospho.log, use phospho.new_task
        to generate a new task_id, or use pospho.latest_task_id.
    :param flag: The flag to set for the task. Either "success" or "failure"
    :param notes: Optional notes to add to the task. For example, the reason for the flag.
    :param source: The source of the feedback, such as "user", "system", "user@mail.com", etc.
    :param raw_flag: The raw flag to set for the task. This can be a more complex object. If
        flag is specified, this is ignored.
    :param raw_flag_to_flag: A function to convert the raw_flag to a flag. If flag is specified,
        this is ignored.
    """

    if flag is None:
        if raw_flag is None:
            logger.warning(
                "Either flag or raw_flag must be specified when calling user_feedback. Nothing logged"
            )
            return
        else:
            if raw_flag_to_flag is None:
                # Default behaviour: some values are mapped to success, others to failure
                if raw_flag in ["success", "👍", "🙂", "😀"]:
                    flag = "success"
                else:
                    flag = "failure"
            else:
                # Use the custom function
                flag = raw_flag_to_flag(raw_flag)

    # Call the client
    current_task = Task(client=client, task_id=task_id, _content=None)
    updated_task = current_task.update(flag=flag, flag_source=source, notes=notes)
    return updated_task


def flush() -> None:
    """
    Flush the log_queue. This will send all the logs to phospho.
    """
    global consumer

    consumer.send_batch()
