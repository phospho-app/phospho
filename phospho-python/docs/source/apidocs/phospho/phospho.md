# {py:mod}`phospho`

```{py:module} phospho
```

```{autodoc2-docstring} phospho
:allowtitles:
```

## Subpackages

```{toctree}
:titlesonly:
:maxdepth: 3

phospho.lab
```

## Submodules

```{toctree}
:titlesonly:
:maxdepth: 1

phospho.sessions
phospho.tasks
phospho.config
phospho.models
phospho.client
phospho.extractor
phospho.utils
phospho.collection
phospho.testing
phospho.integrations
```

## Package Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`init <phospho.init>`
  - ```{autodoc2-docstring} phospho.init
    :summary:
    ```
* - {py:obj}`new_session <phospho.new_session>`
  - ```{autodoc2-docstring} phospho.new_session
    :summary:
    ```
* - {py:obj}`new_task <phospho.new_task>`
  - ```{autodoc2-docstring} phospho.new_task
    :summary:
    ```
* - {py:obj}`_log_single_event <phospho._log_single_event>`
  - ```{autodoc2-docstring} phospho._log_single_event
    :summary:
    ```
* - {py:obj}`_wrap_iterable <phospho._wrap_iterable>`
  - ```{autodoc2-docstring} phospho._wrap_iterable
    :summary:
    ```
* - {py:obj}`log <phospho.log>`
  - ```{autodoc2-docstring} phospho.log
    :summary:
    ```
* - {py:obj}`_wrap <phospho._wrap>`
  - ```{autodoc2-docstring} phospho._wrap
    :summary:
    ```
* - {py:obj}`wrap <phospho.wrap>`
  - ```{autodoc2-docstring} phospho.wrap
    :summary:
    ```
* - {py:obj}`user_feedback <phospho.user_feedback>`
  - ```{autodoc2-docstring} phospho.user_feedback
    :summary:
    ```
* - {py:obj}`flush <phospho.flush>`
  - ```{autodoc2-docstring} phospho.flush
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`log_queue <phospho.log_queue>`
  - ```{autodoc2-docstring} phospho.log_queue
    :summary:
    ```
* - {py:obj}`consumer <phospho.consumer>`
  - ```{autodoc2-docstring} phospho.consumer
    :summary:
    ```
* - {py:obj}`latest_task_id <phospho.latest_task_id>`
  - ```{autodoc2-docstring} phospho.latest_task_id
    :summary:
    ```
* - {py:obj}`latest_session_id <phospho.latest_session_id>`
  - ```{autodoc2-docstring} phospho.latest_session_id
    :summary:
    ```
* - {py:obj}`logger <phospho.logger>`
  - ```{autodoc2-docstring} phospho.logger
    :summary:
    ```
````

### API

````{py:data} log_queue
:canonical: phospho.log_queue
:value: >
   None

```{autodoc2-docstring} phospho.log_queue
```

````

````{py:data} consumer
:canonical: phospho.consumer
:value: >
   None

```{autodoc2-docstring} phospho.consumer
```

````

````{py:data} latest_task_id
:canonical: phospho.latest_task_id
:value: >
   None

```{autodoc2-docstring} phospho.latest_task_id
```

````

````{py:data} latest_session_id
:canonical: phospho.latest_session_id
:value: >
   None

```{autodoc2-docstring} phospho.latest_session_id
```

````

````{py:data} logger
:canonical: phospho.logger
:value: >
   'getLogger(...)'

```{autodoc2-docstring} phospho.logger
```

````

````{py:function} init(api_key: typing.Optional[str] = None, project_id: typing.Optional[str] = None, base_url: typing.Optional[str] = None, tick: float = 0.5, raise_error_on_fail_to_send: bool = False) -> None
:canonical: phospho.init

```{autodoc2-docstring} phospho.init
```
````

````{py:function} new_session() -> str
:canonical: phospho.new_session

```{autodoc2-docstring} phospho.new_session
```
````

````{py:function} new_task() -> str
:canonical: phospho.new_task

```{autodoc2-docstring} phospho.new_task
```
````

````{py:function} _log_single_event(input: typing.Union[phospho.extractor.RawDataType, str], output: typing.Optional[typing.Union[phospho.extractor.RawDataType, str]] = None, session_id: typing.Optional[str] = None, task_id: typing.Optional[str] = None, raw_input: typing.Optional[phospho.extractor.RawDataType] = None, raw_output: typing.Optional[phospho.extractor.RawDataType] = None, input_to_str_function: typing.Optional[typing.Callable[[typing.Any], str]] = None, output_to_str_function: typing.Optional[typing.Callable[[typing.Any], str]] = None, concatenate_raw_outputs_if_task_id_exists: bool = True, input_output_to_usage_function: typing.Optional[typing.Callable[[typing.Any, typing.Any], typing.Dict[str, float]]] = None, to_log: bool = True, **kwargs: typing.Any) -> typing.Dict[str, object]
:canonical: phospho._log_single_event

```{autodoc2-docstring} phospho._log_single_event
```
````

````{py:function} _wrap_iterable(output: typing.Union[typing.Iterable[phospho.extractor.RawDataType], typing.AsyncIterable[phospho.extractor.RawDataType]]) -> None
:canonical: phospho._wrap_iterable

```{autodoc2-docstring} phospho._wrap_iterable
```
````

````{py:function} log(input: typing.Union[phospho.extractor.RawDataType, str], output: typing.Optional[typing.Union[phospho.extractor.RawDataType, str, typing.Iterable[phospho.extractor.RawDataType]]] = None, session_id: typing.Optional[str] = None, task_id: typing.Optional[str] = None, version_id: typing.Optional[str] = None, user_id: typing.Optional[str] = None, raw_input: typing.Optional[phospho.extractor.RawDataType] = None, raw_output: typing.Optional[phospho.extractor.RawDataType] = None, input_to_str_function: typing.Optional[typing.Callable[[typing.Any], str]] = None, output_to_str_function: typing.Optional[typing.Callable[[typing.Any], str]] = None, concatenate_raw_outputs_if_task_id_exists: bool = True, input_output_to_usage_function: typing.Optional[typing.Callable[[typing.Any], typing.Dict[str, float]]] = None, stream: bool = False, **kwargs: typing.Any) -> typing.Optional[typing.Dict[str, object]]
:canonical: phospho.log

```{autodoc2-docstring} phospho.log
```
````

````{py:function} _wrap(__fn, stream: bool = False, stop: typing.Optional[typing.Callable[[typing.Any], bool]] = None, **meta_wrap_kwargs: typing.Any) -> typing.Callable[[typing.Any], typing.Any]
:canonical: phospho._wrap

```{autodoc2-docstring} phospho._wrap
```
````

````{py:function} wrap(__fn: typing.Optional[typing.Callable[[typing.Any], typing.Any]] = None, *, stream: bool = False, stop: typing.Optional[typing.Callable[[typing.Any], bool]] = None, **meta_kwargs)
:canonical: phospho.wrap

```{autodoc2-docstring} phospho.wrap
```
````

````{py:function} user_feedback(task_id: str, flag: typing.Optional[typing.Literal[success, failure]] = None, notes: typing.Optional[str] = None, source: str = 'user', raw_flag: typing.Optional[str] = None, raw_flag_to_flag: typing.Optional[typing.Callable[[typing.Any], typing.Literal[success, failure]]] = None) -> typing.Optional[phospho.tasks.Task]
:canonical: phospho.user_feedback

```{autodoc2-docstring} phospho.user_feedback
```
````

````{py:function} flush() -> None
:canonical: phospho.flush

```{autodoc2-docstring} phospho.flush
```
````
