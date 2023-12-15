# {py:mod}`phospho.client`

```{py:module} phospho.client
```

```{autodoc2-docstring} phospho.client
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`Client <phospho.client.Client>`
  - ```{autodoc2-docstring} phospho.client.Client
    :summary:
    ```
````

### API

`````{py:class} Client(api_key: typing.Optional[str] = None, project_id: typing.Optional[str] = None, base_url: typing.Optional[str] = None)
:canonical: phospho.client.Client

```{autodoc2-docstring} phospho.client.Client
```

```{rubric} Initialization
```

```{autodoc2-docstring} phospho.client.Client.__init__
```

````{py:method} _api_key() -> str
:canonical: phospho.client.Client._api_key

```{autodoc2-docstring} phospho.client.Client._api_key
```

````

````{py:method} _project_id() -> str
:canonical: phospho.client.Client._project_id

```{autodoc2-docstring} phospho.client.Client._project_id
```

````

````{py:method} _headers() -> typing.Dict[str, str]
:canonical: phospho.client.Client._headers

```{autodoc2-docstring} phospho.client.Client._headers
```

````

````{py:method} _get(path: str, params: typing.Optional[typing.Dict[str, str]] = None) -> requests.Response
:canonical: phospho.client.Client._get

```{autodoc2-docstring} phospho.client.Client._get
```

````

````{py:method} _post(path: str, payload: typing.Optional[typing.Dict[str, object]] = None) -> requests.Response
:canonical: phospho.client.Client._post

```{autodoc2-docstring} phospho.client.Client._post
```

````

````{py:property} sessions
:canonical: phospho.client.Client.sessions
:type: phospho.sessions.SessionCollection

```{autodoc2-docstring} phospho.client.Client.sessions
```

````

````{py:property} tasks
:canonical: phospho.client.Client.tasks
:type: phospho.tasks.TaskCollection

```{autodoc2-docstring} phospho.client.Client.tasks
```

````

````{py:method} compare(context_input: str, old_output: str, new_output: str) -> phospho.evals.Comparison
:canonical: phospho.client.Client.compare

```{autodoc2-docstring} phospho.client.Client.compare
```

````

`````
