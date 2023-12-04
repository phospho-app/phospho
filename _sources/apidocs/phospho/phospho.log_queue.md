# {py:mod}`phospho.log_queue`

```{py:module} phospho.log_queue
```

```{autodoc2-docstring} phospho.log_queue
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`Event <phospho.log_queue.Event>`
  -
* - {py:obj}`LogQueue <phospho.log_queue.LogQueue>`
  - ```{autodoc2-docstring} phospho.log_queue.LogQueue
    :summary:
    ```
````

### API

`````{py:class} Event(**data: typing.Any)
:canonical: phospho.log_queue.Event

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} id
:canonical: phospho.log_queue.Event.id
:type: str
:value: >
   None

```{autodoc2-docstring} phospho.log_queue.Event.id
```

````

````{py:attribute} content
:canonical: phospho.log_queue.Event.content
:type: typing.Dict[str, object]
:value: >
   None

```{autodoc2-docstring} phospho.log_queue.Event.content
```

````

````{py:attribute} to_log
:canonical: phospho.log_queue.Event.to_log
:type: bool
:value: >
   True

```{autodoc2-docstring} phospho.log_queue.Event.to_log
```

````

`````

`````{py:class} LogQueue()
:canonical: phospho.log_queue.LogQueue

```{autodoc2-docstring} phospho.log_queue.LogQueue
```

```{rubric} Initialization
```

```{autodoc2-docstring} phospho.log_queue.LogQueue.__init__
```

````{py:method} append(event: phospho.log_queue.Event) -> None
:canonical: phospho.log_queue.LogQueue.append

```{autodoc2-docstring} phospho.log_queue.LogQueue.append
```

````

````{py:method} extend(events_queue: typing.Dict[str, phospho.log_queue.Event]) -> None
:canonical: phospho.log_queue.LogQueue.extend

```{autodoc2-docstring} phospho.log_queue.LogQueue.extend
```

````

````{py:method} add_batch(events_content_list: typing.List[typing.Dict[str, object]]) -> None
:canonical: phospho.log_queue.LogQueue.add_batch

```{autodoc2-docstring} phospho.log_queue.LogQueue.add_batch
```

````

````{py:method} get_batch() -> typing.List[typing.Dict[str, object]]
:canonical: phospho.log_queue.LogQueue.get_batch

```{autodoc2-docstring} phospho.log_queue.LogQueue.get_batch
```

````

`````
