# {py:mod}`phospho.lab.models`

```{py:module} phospho.lab.models
```

```{autodoc2-docstring} phospho.lab.models
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`Message <phospho.lab.models.Message>`
  -
* - {py:obj}`ResultType <phospho.lab.models.ResultType>`
  -
* - {py:obj}`JobResult <phospho.lab.models.JobResult>`
  -
* - {py:obj}`JobConfig <phospho.lab.models.JobConfig>`
  - ```{autodoc2-docstring} phospho.lab.models.JobConfig
    :summary:
    ```
* - {py:obj}`EventDetectionConfig <phospho.lab.models.EventDetectionConfig>`
  -
* - {py:obj}`EvalConfig <phospho.lab.models.EvalConfig>`
  -
* - {py:obj}`EventConfig <phospho.lab.models.EventConfig>`
  -
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`logger <phospho.lab.models.logger>`
  - ```{autodoc2-docstring} phospho.lab.models.logger
    :summary:
    ```
````

### API

````{py:data} logger
:canonical: phospho.lab.models.logger
:value: >
   'getLogger(...)'

```{autodoc2-docstring} phospho.lab.models.logger
```

````

`````{py:class} Message(/, **data: typing.Any)
:canonical: phospho.lab.models.Message

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} id
:canonical: phospho.lab.models.Message.id
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} phospho.lab.models.Message.id
```

````

````{py:attribute} created_at
:canonical: phospho.lab.models.Message.created_at
:type: int
:value: >
   'Field(...)'

```{autodoc2-docstring} phospho.lab.models.Message.created_at
```

````

````{py:attribute} role
:canonical: phospho.lab.models.Message.role
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} phospho.lab.models.Message.role
```

````

````{py:attribute} content
:canonical: phospho.lab.models.Message.content
:type: str
:value: >
   None

```{autodoc2-docstring} phospho.lab.models.Message.content
```

````

````{py:attribute} previous_messages
:canonical: phospho.lab.models.Message.previous_messages
:type: typing.List[phospho.lab.models.Message]
:value: >
   'Field(...)'

```{autodoc2-docstring} phospho.lab.models.Message.previous_messages
```

````

````{py:attribute} metadata
:canonical: phospho.lab.models.Message.metadata
:type: dict
:value: >
   'Field(...)'

```{autodoc2-docstring} phospho.lab.models.Message.metadata
```

````

````{py:method} transcript(with_role: bool = True, with_previous_messages: bool = False, only_previous_messages: bool = False) -> str
:canonical: phospho.lab.models.Message.transcript

```{autodoc2-docstring} phospho.lab.models.Message.transcript
```

````

````{py:method} previous_messages_transcript(with_role: bool = True) -> typing.Optional[str]
:canonical: phospho.lab.models.Message.previous_messages_transcript

```{autodoc2-docstring} phospho.lab.models.Message.previous_messages_transcript
```

````

````{py:method} latest_interaction() -> str
:canonical: phospho.lab.models.Message.latest_interaction

```{autodoc2-docstring} phospho.lab.models.Message.latest_interaction
```

````

````{py:method} latest_interaction_context() -> typing.Optional[str]
:canonical: phospho.lab.models.Message.latest_interaction_context

```{autodoc2-docstring} phospho.lab.models.Message.latest_interaction_context
```

````

`````

`````{py:class} ResultType(*args, **kwds)
:canonical: phospho.lab.models.ResultType

Bases: {py:obj}`enum.Enum`

````{py:attribute} error
:canonical: phospho.lab.models.ResultType.error
:value: >
   'error'

```{autodoc2-docstring} phospho.lab.models.ResultType.error
```

````

````{py:attribute} bool
:canonical: phospho.lab.models.ResultType.bool
:value: >
   'bool'

```{autodoc2-docstring} phospho.lab.models.ResultType.bool
```

````

````{py:attribute} literal
:canonical: phospho.lab.models.ResultType.literal
:value: >
   'literal'

```{autodoc2-docstring} phospho.lab.models.ResultType.literal
```

````

`````

`````{py:class} JobResult(/, **data: typing.Any)
:canonical: phospho.lab.models.JobResult

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} created_at
:canonical: phospho.lab.models.JobResult.created_at
:type: int
:value: >
   'Field(...)'

```{autodoc2-docstring} phospho.lab.models.JobResult.created_at
```

````

````{py:attribute} job_id
:canonical: phospho.lab.models.JobResult.job_id
:type: str
:value: >
   None

```{autodoc2-docstring} phospho.lab.models.JobResult.job_id
```

````

````{py:attribute} result_type
:canonical: phospho.lab.models.JobResult.result_type
:type: phospho.lab.models.ResultType
:value: >
   None

```{autodoc2-docstring} phospho.lab.models.JobResult.result_type
```

````

````{py:attribute} value
:canonical: phospho.lab.models.JobResult.value
:type: typing.Any
:value: >
   None

```{autodoc2-docstring} phospho.lab.models.JobResult.value
```

````

````{py:attribute} logs
:canonical: phospho.lab.models.JobResult.logs
:type: typing.List[typing.Any]
:value: >
   'Field(...)'

```{autodoc2-docstring} phospho.lab.models.JobResult.logs
```

````

````{py:attribute} metadata
:canonical: phospho.lab.models.JobResult.metadata
:type: dict
:value: >
   'Field(...)'

```{autodoc2-docstring} phospho.lab.models.JobResult.metadata
```

````

`````

`````{py:class} JobConfig(/, **data: typing.Any)
:canonical: phospho.lab.models.JobConfig

Bases: {py:obj}`pydantic.BaseModel`

```{autodoc2-docstring} phospho.lab.models.JobConfig
```

```{rubric} Initialization
```

```{autodoc2-docstring} phospho.lab.models.JobConfig.__init__
```

````{py:method} generate_configurations(exclude_default: bool = True) -> typing.List[phospho.lab.models.JobConfig]
:canonical: phospho.lab.models.JobConfig.generate_configurations

```{autodoc2-docstring} phospho.lab.models.JobConfig.generate_configurations
```

````

`````

`````{py:class} EventDetectionConfig(/, **data: typing.Any)
:canonical: phospho.lab.models.EventDetectionConfig

Bases: {py:obj}`phospho.lab.models.JobConfig`

````{py:attribute} model
:canonical: phospho.lab.models.EventDetectionConfig.model
:type: typing.Literal[gpt-4, gpt-3.5-turbo]
:value: >
   'gpt-4'

```{autodoc2-docstring} phospho.lab.models.EventDetectionConfig.model
```

````

`````

`````{py:class} EvalConfig(/, **data: typing.Any)
:canonical: phospho.lab.models.EvalConfig

Bases: {py:obj}`phospho.lab.models.JobConfig`

````{py:attribute} model
:canonical: phospho.lab.models.EvalConfig.model
:type: typing.Literal[gpt-4, gpt-3.5-turbo]
:value: >
   'gpt-4'

```{autodoc2-docstring} phospho.lab.models.EvalConfig.model
```

````

````{py:attribute} metadata
:canonical: phospho.lab.models.EvalConfig.metadata
:type: dict
:value: >
   'Field(...)'

```{autodoc2-docstring} phospho.lab.models.EvalConfig.metadata
```

````

`````

`````{py:class} EventConfig(/, **data: typing.Any)
:canonical: phospho.lab.models.EventConfig

Bases: {py:obj}`phospho.lab.models.JobConfig`

````{py:attribute} event_name
:canonical: phospho.lab.models.EventConfig.event_name
:type: str
:value: >
   None

```{autodoc2-docstring} phospho.lab.models.EventConfig.event_name
```

````

````{py:attribute} event_description
:canonical: phospho.lab.models.EventConfig.event_description
:type: str
:value: >
   None

```{autodoc2-docstring} phospho.lab.models.EventConfig.event_description
```

````

`````
