# {py:mod}`phospho.models`

```{py:module} phospho.models
```

```{autodoc2-docstring} phospho.models
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`EvalModel <phospho.models.EvalModel>`
  -
* - {py:obj}`TaskModel <phospho.models.TaskModel>`
  -
* - {py:obj}`Test <phospho.models.Test>`
  -
* - {py:obj}`Comparison <phospho.models.Comparison>`
  -
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`ComparisonResults <phospho.models.ComparisonResults>`
  - ```{autodoc2-docstring} phospho.models.ComparisonResults
    :summary:
    ```
````

### API

`````{py:class} EvalModel(**data: typing.Any)
:canonical: phospho.models.EvalModel

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} id
:canonical: phospho.models.EvalModel.id
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} phospho.models.EvalModel.id
```

````

````{py:attribute} created_at
:canonical: phospho.models.EvalModel.created_at
:type: int
:value: >
   'Field(...)'

```{autodoc2-docstring} phospho.models.EvalModel.created_at
```

````

````{py:attribute} project_id
:canonical: phospho.models.EvalModel.project_id
:type: str
:value: >
   None

```{autodoc2-docstring} phospho.models.EvalModel.project_id
```

````

````{py:attribute} session_id
:canonical: phospho.models.EvalModel.session_id
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} phospho.models.EvalModel.session_id
```

````

````{py:attribute} task_id
:canonical: phospho.models.EvalModel.task_id
:type: str
:value: >
   None

```{autodoc2-docstring} phospho.models.EvalModel.task_id
```

````

````{py:attribute} value
:canonical: phospho.models.EvalModel.value
:type: typing.Literal[success, failure, undefined]
:value: >
   None

```{autodoc2-docstring} phospho.models.EvalModel.value
```

````

````{py:attribute} source
:canonical: phospho.models.EvalModel.source
:type: str
:value: >
   None

```{autodoc2-docstring} phospho.models.EvalModel.source
```

````

`````

`````{py:class} TaskModel(**data: typing.Any)
:canonical: phospho.models.TaskModel

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} id
:canonical: phospho.models.TaskModel.id
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} phospho.models.TaskModel.id
```

````

````{py:attribute} created_at
:canonical: phospho.models.TaskModel.created_at
:type: int
:value: >
   'Field(...)'

```{autodoc2-docstring} phospho.models.TaskModel.created_at
```

````

````{py:attribute} project_id
:canonical: phospho.models.TaskModel.project_id
:type: str
:value: >
   None

```{autodoc2-docstring} phospho.models.TaskModel.project_id
```

````

````{py:attribute} session_id
:canonical: phospho.models.TaskModel.session_id
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} phospho.models.TaskModel.session_id
```

````

````{py:attribute} input
:canonical: phospho.models.TaskModel.input
:type: str
:value: >
   None

```{autodoc2-docstring} phospho.models.TaskModel.input
```

````

````{py:attribute} additional_input
:canonical: phospho.models.TaskModel.additional_input
:type: typing.Optional[dict]
:value: >
   'Field(...)'

```{autodoc2-docstring} phospho.models.TaskModel.additional_input
```

````

````{py:attribute} output
:canonical: phospho.models.TaskModel.output
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} phospho.models.TaskModel.output
```

````

````{py:attribute} additional_output
:canonical: phospho.models.TaskModel.additional_output
:type: typing.Optional[dict]
:value: >
   'Field(...)'

```{autodoc2-docstring} phospho.models.TaskModel.additional_output
```

````

````{py:attribute} metadata
:canonical: phospho.models.TaskModel.metadata
:type: typing.Optional[dict]
:value: >
   'Field(...)'

```{autodoc2-docstring} phospho.models.TaskModel.metadata
```

````

````{py:attribute} data
:canonical: phospho.models.TaskModel.data
:type: typing.Optional[dict]
:value: >
   'Field(...)'

```{autodoc2-docstring} phospho.models.TaskModel.data
```

````

````{py:attribute} flag
:canonical: phospho.models.TaskModel.flag
:type: typing.Optional[typing.Literal[success, failure]]
:value: >
   None

```{autodoc2-docstring} phospho.models.TaskModel.flag
```

````

````{py:attribute} last_eval
:canonical: phospho.models.TaskModel.last_eval
:type: typing.Optional[phospho.models.EvalModel]
:value: >
   None

```{autodoc2-docstring} phospho.models.TaskModel.last_eval
```

````

````{py:attribute} events
:canonical: phospho.models.TaskModel.events
:type: typing.Optional[typing.List]
:value: >
   'Field(...)'

```{autodoc2-docstring} phospho.models.TaskModel.events
```

````

````{py:attribute} environment
:canonical: phospho.models.TaskModel.environment
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} phospho.models.TaskModel.environment
```

````

`````

`````{py:class} Test(**data: typing.Any)
:canonical: phospho.models.Test

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} id
:canonical: phospho.models.Test.id
:type: str
:value: >
   'Field(...)'

```{autodoc2-docstring} phospho.models.Test.id
```

````

````{py:attribute} project_id
:canonical: phospho.models.Test.project_id
:type: str
:value: >
   None

```{autodoc2-docstring} phospho.models.Test.project_id
```

````

````{py:attribute} created_by
:canonical: phospho.models.Test.created_by
:type: str
:value: >
   None

```{autodoc2-docstring} phospho.models.Test.created_by
```

````

````{py:attribute} created_at
:canonical: phospho.models.Test.created_at
:type: int
:value: >
   'Field(...)'

```{autodoc2-docstring} phospho.models.Test.created_at
```

````

````{py:attribute} last_updated_at
:canonical: phospho.models.Test.last_updated_at
:type: int
:value: >
   None

```{autodoc2-docstring} phospho.models.Test.last_updated_at
```

````

````{py:attribute} terminated_at
:canonical: phospho.models.Test.terminated_at
:type: typing.Optional[int]
:value: >
   None

```{autodoc2-docstring} phospho.models.Test.terminated_at
```

````

````{py:attribute} status
:canonical: phospho.models.Test.status
:type: typing.Literal[started, completed, canceled]
:value: >
   None

```{autodoc2-docstring} phospho.models.Test.status
```

````

````{py:attribute} summary
:canonical: phospho.models.Test.summary
:type: dict
:value: >
   'Field(...)'

```{autodoc2-docstring} phospho.models.Test.summary
```

````

`````

````{py:data} ComparisonResults
:canonical: phospho.models.ComparisonResults
:value: >
   None

```{autodoc2-docstring} phospho.models.ComparisonResults
```

````

`````{py:class} Comparison(**data: typing.Any)
:canonical: phospho.models.Comparison

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} id
:canonical: phospho.models.Comparison.id
:type: str
:value: >
   None

```{autodoc2-docstring} phospho.models.Comparison.id
```

````

````{py:attribute} created_at
:canonical: phospho.models.Comparison.created_at
:type: int
:value: >
   None

```{autodoc2-docstring} phospho.models.Comparison.created_at
```

````

````{py:attribute} project_id
:canonical: phospho.models.Comparison.project_id
:type: str
:value: >
   None

```{autodoc2-docstring} phospho.models.Comparison.project_id
```

````

````{py:attribute} instructions
:canonical: phospho.models.Comparison.instructions
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} phospho.models.Comparison.instructions
```

````

````{py:attribute} context_input
:canonical: phospho.models.Comparison.context_input
:type: str
:value: >
   None

```{autodoc2-docstring} phospho.models.Comparison.context_input
```

````

````{py:attribute} old_output
:canonical: phospho.models.Comparison.old_output
:type: str
:value: >
   None

```{autodoc2-docstring} phospho.models.Comparison.old_output
```

````

````{py:attribute} new_output
:canonical: phospho.models.Comparison.new_output
:type: str
:value: >
   None

```{autodoc2-docstring} phospho.models.Comparison.new_output
```

````

````{py:attribute} comparison_result
:canonical: phospho.models.Comparison.comparison_result
:type: phospho.models.ComparisonResults
:value: >
   None

```{autodoc2-docstring} phospho.models.Comparison.comparison_result
```

````

````{py:attribute} source
:canonical: phospho.models.Comparison.source
:type: str
:value: >
   None

```{autodoc2-docstring} phospho.models.Comparison.source
```

````

`````
