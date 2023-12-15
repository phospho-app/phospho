# {py:mod}`phospho.evals`

```{py:module} phospho.evals
```

```{autodoc2-docstring} phospho.evals
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`Comparison <phospho.evals.Comparison>`
  -
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`ComparisonResults <phospho.evals.ComparisonResults>`
  - ```{autodoc2-docstring} phospho.evals.ComparisonResults
    :summary:
    ```
````

### API

````{py:data} ComparisonResults
:canonical: phospho.evals.ComparisonResults
:value: >
   None

```{autodoc2-docstring} phospho.evals.ComparisonResults
```

````

`````{py:class} Comparison(**data: typing.Any)
:canonical: phospho.evals.Comparison

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} id
:canonical: phospho.evals.Comparison.id
:type: str
:value: >
   None

```{autodoc2-docstring} phospho.evals.Comparison.id
```

````

````{py:attribute} created_at
:canonical: phospho.evals.Comparison.created_at
:type: int
:value: >
   None

```{autodoc2-docstring} phospho.evals.Comparison.created_at
```

````

````{py:attribute} project_id
:canonical: phospho.evals.Comparison.project_id
:type: str
:value: >
   None

```{autodoc2-docstring} phospho.evals.Comparison.project_id
```

````

````{py:attribute} instructions
:canonical: phospho.evals.Comparison.instructions
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} phospho.evals.Comparison.instructions
```

````

````{py:attribute} context_input
:canonical: phospho.evals.Comparison.context_input
:type: str
:value: >
   None

```{autodoc2-docstring} phospho.evals.Comparison.context_input
```

````

````{py:attribute} old_output
:canonical: phospho.evals.Comparison.old_output
:type: str
:value: >
   None

```{autodoc2-docstring} phospho.evals.Comparison.old_output
```

````

````{py:attribute} new_output
:canonical: phospho.evals.Comparison.new_output
:type: str
:value: >
   None

```{autodoc2-docstring} phospho.evals.Comparison.new_output
```

````

````{py:attribute} comparison_result
:canonical: phospho.evals.Comparison.comparison_result
:type: phospho.evals.ComparisonResults
:value: >
   None

```{autodoc2-docstring} phospho.evals.Comparison.comparison_result
```

````

````{py:attribute} source
:canonical: phospho.evals.Comparison.source
:type: str
:value: >
   None

```{autodoc2-docstring} phospho.evals.Comparison.source
```

````

`````
