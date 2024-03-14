# {py:mod}`phospho.lab.job_library`

```{py:module} phospho.lab.job_library
```

```{autodoc2-docstring} phospho.lab.job_library
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`prompt_to_bool <phospho.lab.job_library.prompt_to_bool>`
  - ```{autodoc2-docstring} phospho.lab.job_library.prompt_to_bool
    :summary:
    ```
* - {py:obj}`prompt_to_literal <phospho.lab.job_library.prompt_to_literal>`
  - ```{autodoc2-docstring} phospho.lab.job_library.prompt_to_literal
    :summary:
    ```
* - {py:obj}`event_detection <phospho.lab.job_library.event_detection>`
  - ```{autodoc2-docstring} phospho.lab.job_library.event_detection
    :summary:
    ```
* - {py:obj}`evaluate_task <phospho.lab.job_library.evaluate_task>`
  - ```{autodoc2-docstring} phospho.lab.job_library.evaluate_task
    :summary:
    ```
* - {py:obj}`get_nb_tokens <phospho.lab.job_library.get_nb_tokens>`
  - ```{autodoc2-docstring} phospho.lab.job_library.get_nb_tokens
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`logger <phospho.lab.job_library.logger>`
  - ```{autodoc2-docstring} phospho.lab.job_library.logger
    :summary:
    ```
````

### API

````{py:data} logger
:canonical: phospho.lab.job_library.logger
:value: >
   'getLogger(...)'

```{autodoc2-docstring} phospho.lab.job_library.logger
```

````

````{py:function} prompt_to_bool(message: phospho.lab.models.Message, prompt: str, format_kwargs: typing.Optional[dict] = None, model: str = 'openai:gpt-3.5-turbo') -> phospho.lab.models.JobResult
:canonical: phospho.lab.job_library.prompt_to_bool

```{autodoc2-docstring} phospho.lab.job_library.prompt_to_bool
```
````

````{py:function} prompt_to_literal(message: phospho.lab.models.Message, prompt: str, output_literal: typing.List[str], format_kwargs: typing.Optional[dict] = None, model: str = 'openai:gpt-3.5-turbo') -> phospho.lab.models.JobResult
:canonical: phospho.lab.job_library.prompt_to_literal

```{autodoc2-docstring} phospho.lab.job_library.prompt_to_literal
```
````

````{py:function} event_detection(message: phospho.lab.models.Message, event_name: str, event_description: str, model: str = 'openai:gpt-3.5-turbo') -> phospho.lab.models.JobResult
:canonical: phospho.lab.job_library.event_detection
:async:

```{autodoc2-docstring} phospho.lab.job_library.event_detection
```
````

````{py:function} evaluate_task(message: phospho.lab.models.Message, few_shot_min_number_of_examples: int = 5, few_shot_max_number_of_examples: int = 10, model: str = 'openai:gpt-4-1106-preview') -> phospho.lab.models.JobResult
:canonical: phospho.lab.job_library.evaluate_task
:async:

```{autodoc2-docstring} phospho.lab.job_library.evaluate_task
```
````

````{py:function} get_nb_tokens(message: phospho.lab.models.Message, model: typing.Optional[str] = 'openai:gpt-3.5-turbo-0613', tokenizer=None) -> phospho.lab.models.JobResult
:canonical: phospho.lab.job_library.get_nb_tokens

```{autodoc2-docstring} phospho.lab.job_library.get_nb_tokens
```
````
