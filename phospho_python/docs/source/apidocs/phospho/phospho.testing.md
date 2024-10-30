# {py:mod}`phospho.testing`

```{py:module} phospho.testing
```

```{autodoc2-docstring} phospho.testing
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`TestInput <phospho.testing.TestInput>`
  -
* - {py:obj}`BacktestLoader <phospho.testing.BacktestLoader>`
  - ```{autodoc2-docstring} phospho.testing.BacktestLoader
    :summary:
    ```
* - {py:obj}`DatasetLoader <phospho.testing.DatasetLoader>`
  - ```{autodoc2-docstring} phospho.testing.DatasetLoader
    :summary:
    ```
* - {py:obj}`PhosphoTest <phospho.testing.PhosphoTest>`
  - ```{autodoc2-docstring} phospho.testing.PhosphoTest
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`adapt_dict_to_agent_function <phospho.testing.adapt_dict_to_agent_function>`
  - ```{autodoc2-docstring} phospho.testing.adapt_dict_to_agent_function
    :summary:
    ```
* - {py:obj}`adapt_task_to_agent_function <phospho.testing.adapt_task_to_agent_function>`
  - ```{autodoc2-docstring} phospho.testing.adapt_task_to_agent_function
    :summary:
    ```
* - {py:obj}`adapt_to_sample_size <phospho.testing.adapt_to_sample_size>`
  - ```{autodoc2-docstring} phospho.testing.adapt_to_sample_size
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`logger <phospho.testing.logger>`
  - ```{autodoc2-docstring} phospho.testing.logger
    :summary:
    ```
````

### API

````{py:data} logger
:canonical: phospho.testing.logger
:value: >
   'getLogger(...)'

```{autodoc2-docstring} phospho.testing.logger
```

````

`````{py:class} TestInput(/, **data: typing.Any)
:canonical: phospho.testing.TestInput

Bases: {py:obj}`pydantic.BaseModel`

````{py:attribute} function_input
:canonical: phospho.testing.TestInput.function_input
:type: dict
:value: >
   None

```{autodoc2-docstring} phospho.testing.TestInput.function_input
```

````

````{py:attribute} input
:canonical: phospho.testing.TestInput.input
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} phospho.testing.TestInput.input
```

````

````{py:attribute} additional_input
:canonical: phospho.testing.TestInput.additional_input
:type: typing.Optional[dict]
:value: >
   None

```{autodoc2-docstring} phospho.testing.TestInput.additional_input
```

````

````{py:attribute} output
:canonical: phospho.testing.TestInput.output
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} phospho.testing.TestInput.output
```

````

````{py:attribute} task_id
:canonical: phospho.testing.TestInput.task_id
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} phospho.testing.TestInput.task_id
```

````

````{py:method} from_task(task: phospho.tasks.Task) -> phospho.testing.TestInput
:canonical: phospho.testing.TestInput.from_task
:classmethod:

```{autodoc2-docstring} phospho.testing.TestInput.from_task
```

````

`````

````{py:function} adapt_dict_to_agent_function(dict_to_adapt: dict, agent_function: typing.Callable[[typing.Any], typing.Any]) -> typing.Optional[dict]
:canonical: phospho.testing.adapt_dict_to_agent_function

```{autodoc2-docstring} phospho.testing.adapt_dict_to_agent_function
```
````

````{py:function} adapt_task_to_agent_function(task: phospho.tasks.Task, agent_function: typing.Callable[[typing.Any], typing.Any]) -> typing.Optional[phospho.testing.TestInput]
:canonical: phospho.testing.adapt_task_to_agent_function

```{autodoc2-docstring} phospho.testing.adapt_task_to_agent_function
```
````

````{py:function} adapt_to_sample_size(list_to_sample, sample_size)
:canonical: phospho.testing.adapt_to_sample_size

```{autodoc2-docstring} phospho.testing.adapt_to_sample_size
```
````

`````{py:class} BacktestLoader(client: phospho.client.Client, agent_function: typing.Callable[[typing.Any], typing.Any], sample_size: typing.Optional[int] = 10)
:canonical: phospho.testing.BacktestLoader

```{autodoc2-docstring} phospho.testing.BacktestLoader
```

```{rubric} Initialization
```

```{autodoc2-docstring} phospho.testing.BacktestLoader.__init__
```

````{py:method} __iter__()
:canonical: phospho.testing.BacktestLoader.__iter__

```{autodoc2-docstring} phospho.testing.BacktestLoader.__iter__
```

````

````{py:method} __next__()
:canonical: phospho.testing.BacktestLoader.__next__

```{autodoc2-docstring} phospho.testing.BacktestLoader.__next__
```

````

````{py:method} __len__()
:canonical: phospho.testing.BacktestLoader.__len__

```{autodoc2-docstring} phospho.testing.BacktestLoader.__len__
```

````

`````

`````{py:class} DatasetLoader(agent_function: typing.Callable[[typing.Any], typing.Any], path: str, test_n_times: typing.Optional[int] = None)
:canonical: phospho.testing.DatasetLoader

```{autodoc2-docstring} phospho.testing.DatasetLoader
```

```{rubric} Initialization
```

```{autodoc2-docstring} phospho.testing.DatasetLoader.__init__
```

````{py:method} __iter__()
:canonical: phospho.testing.DatasetLoader.__iter__

```{autodoc2-docstring} phospho.testing.DatasetLoader.__iter__
```

````

````{py:method} __next__()
:canonical: phospho.testing.DatasetLoader.__next__

```{autodoc2-docstring} phospho.testing.DatasetLoader.__next__
```

````

````{py:method} __len__()
:canonical: phospho.testing.DatasetLoader.__len__

```{autodoc2-docstring} phospho.testing.DatasetLoader.__len__
```

````

`````

`````{py:class} PhosphoTest(api_key: typing.Optional[str] = None, project_id: typing.Optional[str] = None)
:canonical: phospho.testing.PhosphoTest

```{autodoc2-docstring} phospho.testing.PhosphoTest
```

```{rubric} Initialization
```

```{autodoc2-docstring} phospho.testing.PhosphoTest.__init__
```

````{py:attribute} client
:canonical: phospho.testing.PhosphoTest.client
:type: phospho.client.Client
:value: >
   None

```{autodoc2-docstring} phospho.testing.PhosphoTest.client
```

````

````{py:attribute} functions_to_evaluate
:canonical: phospho.testing.PhosphoTest.functions_to_evaluate
:type: typing.Dict[str, typing.Any]
:value: >
   None

```{autodoc2-docstring} phospho.testing.PhosphoTest.functions_to_evaluate
```

````

````{py:attribute} test_id
:canonical: phospho.testing.PhosphoTest.test_id
:type: typing.Optional[str]
:value: >
   None

```{autodoc2-docstring} phospho.testing.PhosphoTest.test_id
```

````

````{py:method} test(fn: typing.Optional[typing.Callable[[typing.Any], typing.Any]] = None, source_loader: typing.Literal[backtest, dataset] = 'backtest', source_loader_params: typing.Optional[typing.Dict[str, typing.Any]] = None, metrics: typing.Optional[typing.List[typing.Literal[compare, evaluate]]] = None) -> typing.Callable[[typing.Any], typing.Any]
:canonical: phospho.testing.PhosphoTest.test

```{autodoc2-docstring} phospho.testing.PhosphoTest.test
```

````

````{py:method} get_output_from_agent(function_input: typing.Dict[str, typing.Any], agent_function: typing.Callable[[typing.Any], typing.Any], metric_name: str)
:canonical: phospho.testing.PhosphoTest.get_output_from_agent

```{autodoc2-docstring} phospho.testing.PhosphoTest.get_output_from_agent
```

````

````{py:method} evaluate(task_to_evaluate: typing.Dict[str, typing.Any])
:canonical: phospho.testing.PhosphoTest.evaluate

```{autodoc2-docstring} phospho.testing.PhosphoTest.evaluate
```

````

````{py:method} compare(task_to_compare: typing.Dict[str, typing.Any]) -> None
:canonical: phospho.testing.PhosphoTest.compare

```{autodoc2-docstring} phospho.testing.PhosphoTest.compare
```

````

````{py:method} run(executor_type: typing.Literal[parallel, sequential] = 'parallel')
:canonical: phospho.testing.PhosphoTest.run

```{autodoc2-docstring} phospho.testing.PhosphoTest.run
```

````

`````
