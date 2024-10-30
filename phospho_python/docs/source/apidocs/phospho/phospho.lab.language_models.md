# {py:mod}`phospho.lab.language_models`

```{py:module} phospho.lab.language_models
```

```{autodoc2-docstring} phospho.lab.language_models
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`get_provider_and_model <phospho.lab.language_models.get_provider_and_model>`
  - ```{autodoc2-docstring} phospho.lab.language_models.get_provider_and_model
    :summary:
    ```
* - {py:obj}`get_async_client <phospho.lab.language_models.get_async_client>`
  - ```{autodoc2-docstring} phospho.lab.language_models.get_async_client
    :summary:
    ```
* - {py:obj}`get_sync_client <phospho.lab.language_models.get_sync_client>`
  - ```{autodoc2-docstring} phospho.lab.language_models.get_sync_client
    :summary:
    ```
````

### API

````{py:function} get_provider_and_model(model: str) -> typing.Tuple[str, str]
:canonical: phospho.lab.language_models.get_provider_and_model

```{autodoc2-docstring} phospho.lab.language_models.get_provider_and_model
```
````

````{py:function} get_async_client(provider: str) -> openai.AsyncOpenAI
:canonical: phospho.lab.language_models.get_async_client

```{autodoc2-docstring} phospho.lab.language_models.get_async_client
```
````

````{py:function} get_sync_client(provider: str) -> openai.OpenAI
:canonical: phospho.lab.language_models.get_sync_client

```{autodoc2-docstring} phospho.lab.language_models.get_sync_client
```
````
