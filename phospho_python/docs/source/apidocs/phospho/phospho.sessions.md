# {py:mod}`phospho.sessions`

```{py:module} phospho.sessions
```

```{autodoc2-docstring} phospho.sessions
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`Session <phospho.sessions.Session>`
  - ```{autodoc2-docstring} phospho.sessions.Session
    :summary:
    ```
* - {py:obj}`SessionCollection <phospho.sessions.SessionCollection>`
  -
````

### API

`````{py:class} Session(client, session_id: str, _content: typing.Optional[dict] = None)
:canonical: phospho.sessions.Session

```{autodoc2-docstring} phospho.sessions.Session
```

```{rubric} Initialization
```

```{autodoc2-docstring} phospho.sessions.Session.__init__
```

````{py:property} id
:canonical: phospho.sessions.Session.id

```{autodoc2-docstring} phospho.sessions.Session.id
```

````

````{py:property} content
:canonical: phospho.sessions.Session.content

```{autodoc2-docstring} phospho.sessions.Session.content
```

````

````{py:method} refresh()
:canonical: phospho.sessions.Session.refresh

```{autodoc2-docstring} phospho.sessions.Session.refresh
```

````

````{py:method} list_tasks()
:canonical: phospho.sessions.Session.list_tasks

```{autodoc2-docstring} phospho.sessions.Session.list_tasks
```

````

`````

`````{py:class} SessionCollection(client)
:canonical: phospho.sessions.SessionCollection

Bases: {py:obj}`phospho.collection.Collection`

````{py:method} get(session_id: str)
:canonical: phospho.sessions.SessionCollection.get

```{autodoc2-docstring} phospho.sessions.SessionCollection.get
```

````

````{py:method} list()
:canonical: phospho.sessions.SessionCollection.list

```{autodoc2-docstring} phospho.sessions.SessionCollection.list
```

````

````{py:method} create(data: typing.Optional[dict] = None)
:canonical: phospho.sessions.SessionCollection.create

```{autodoc2-docstring} phospho.sessions.SessionCollection.create
```

````

`````
