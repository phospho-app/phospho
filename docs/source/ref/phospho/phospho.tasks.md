# {py:mod}`phospho.tasks`

```{py:module} phospho.tasks
```

```{autodoc2-docstring} phospho.tasks
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`Task <phospho.tasks.Task>`
  - ```{autodoc2-docstring} phospho.tasks.Task
    :summary:
    ```
* - {py:obj}`TaskCollection <phospho.tasks.TaskCollection>`
  -
````

### API

`````{py:class} Task(client, task_id: str, _content: typing.Union[typing.Optional[dict], phospho.models.TaskModel] = None)
:canonical: phospho.tasks.Task

```{autodoc2-docstring} phospho.tasks.Task
```

```{rubric} Initialization
```

```{autodoc2-docstring} phospho.tasks.Task.__init__
```

````{py:property} id
:canonical: phospho.tasks.Task.id

```{autodoc2-docstring} phospho.tasks.Task.id
```

````

````{py:property} content
:canonical: phospho.tasks.Task.content

```{autodoc2-docstring} phospho.tasks.Task.content
```

````

````{py:method} content_as_dict() -> dict
:canonical: phospho.tasks.Task.content_as_dict

```{autodoc2-docstring} phospho.tasks.Task.content_as_dict
```

````

````{py:method} refresh() -> None
:canonical: phospho.tasks.Task.refresh

```{autodoc2-docstring} phospho.tasks.Task.refresh
```

````

````{py:method} update(metadata: typing.Optional[dict] = None, data: typing.Optional[dict] = None, notes: typing.Optional[str] = None, flag: typing.Optional[typing.Literal[success, failure]] = None, flag_source: typing.Optional[str] = None)
:canonical: phospho.tasks.Task.update

```{autodoc2-docstring} phospho.tasks.Task.update
```

````

`````

`````{py:class} TaskCollection(client)
:canonical: phospho.tasks.TaskCollection

Bases: {py:obj}`phospho.collection.Collection`

````{py:method} get(task_id: str)
:canonical: phospho.tasks.TaskCollection.get

```{autodoc2-docstring} phospho.tasks.TaskCollection.get
```

````

````{py:method} create(session_id: str, sender_id: str, input: str, output: str, additional_input: typing.Optional[dict] = None, additional_output: typing.Optional[dict] = None, data: typing.Optional[dict] = None)
:canonical: phospho.tasks.TaskCollection.create

```{autodoc2-docstring} phospho.tasks.TaskCollection.create
```

````

````{py:method} get_all() -> typing.List[phospho.tasks.Task]
:canonical: phospho.tasks.TaskCollection.get_all

```{autodoc2-docstring} phospho.tasks.TaskCollection.get_all
```

````

`````
