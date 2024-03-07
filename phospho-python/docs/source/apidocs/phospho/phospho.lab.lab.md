# {py:mod}`phospho.lab.lab`

```{py:module} phospho.lab.lab
```

```{autodoc2-docstring} phospho.lab.lab
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`Job <phospho.lab.lab.Job>`
  - ```{autodoc2-docstring} phospho.lab.lab.Job
    :summary:
    ```
* - {py:obj}`Workload <phospho.lab.lab.Workload>`
  - ```{autodoc2-docstring} phospho.lab.lab.Workload
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`logger <phospho.lab.lab.logger>`
  - ```{autodoc2-docstring} phospho.lab.lab.logger
    :summary:
    ```
````

### API

````{py:data} logger
:canonical: phospho.lab.lab.logger
:value: >
   'getLogger(...)'

```{autodoc2-docstring} phospho.lab.lab.logger
```

````

`````{py:class} Job(id: typing.Optional[str] = None, job_function: typing.Optional[typing.Union[typing.Callable[..., phospho.lab.models.JobResult], typing.Callable[..., typing.Awaitable[phospho.lab.models.JobResult]]]] = None, name: typing.Optional[str] = None, config: typing.Optional[phospho.lab.models.JobConfig] = None)
:canonical: phospho.lab.lab.Job

```{autodoc2-docstring} phospho.lab.lab.Job
```

```{rubric} Initialization
```

```{autodoc2-docstring} phospho.lab.lab.Job.__init__
```

````{py:attribute} id
:canonical: phospho.lab.lab.Job.id
:type: str
:value: >
   None

```{autodoc2-docstring} phospho.lab.lab.Job.id
```

````

````{py:attribute} job_function
:canonical: phospho.lab.lab.Job.job_function
:type: typing.Union[typing.Callable[..., phospho.lab.models.JobResult], typing.Callable[..., typing.Awaitable[phospho.lab.models.JobResult]]]
:value: >
   None

```{autodoc2-docstring} phospho.lab.lab.Job.job_function
```

````

````{py:attribute} config
:canonical: phospho.lab.lab.Job.config
:type: phospho.lab.models.JobConfig
:value: >
   None

```{autodoc2-docstring} phospho.lab.lab.Job.config
```

````

````{py:attribute} results
:canonical: phospho.lab.lab.Job.results
:type: typing.Dict[str, phospho.lab.models.JobResult]
:value: >
   None

```{autodoc2-docstring} phospho.lab.lab.Job.results
```

````

````{py:attribute} alternative_results
:canonical: phospho.lab.lab.Job.alternative_results
:type: typing.List[typing.Dict[str, phospho.lab.models.JobResult]]
:value: >
   None

```{autodoc2-docstring} phospho.lab.lab.Job.alternative_results
```

````

````{py:attribute} alternative_configs
:canonical: phospho.lab.lab.Job.alternative_configs
:type: typing.List[phospho.lab.models.JobConfig]
:value: >
   None

```{autodoc2-docstring} phospho.lab.lab.Job.alternative_configs
```

````

````{py:method} async_run(message: phospho.lab.models.Message) -> phospho.lab.models.JobResult
:canonical: phospho.lab.lab.Job.async_run
:async:

```{autodoc2-docstring} phospho.lab.lab.Job.async_run
```

````

````{py:method} async_run_on_alternative_configurations(message: phospho.lab.models.Message) -> typing.List[typing.Dict[str, phospho.lab.models.JobResult]]
:canonical: phospho.lab.lab.Job.async_run_on_alternative_configurations
:async:

```{autodoc2-docstring} phospho.lab.lab.Job.async_run_on_alternative_configurations
```

````

````{py:method} optimize(accuracy_threshold: float = 1.0, min_count: int = 10) -> None
:canonical: phospho.lab.lab.Job.optimize

```{autodoc2-docstring} phospho.lab.lab.Job.optimize
```

````

````{py:method} __repr__()
:canonical: phospho.lab.lab.Job.__repr__

````

`````

`````{py:class} Workload()
:canonical: phospho.lab.lab.Workload

```{autodoc2-docstring} phospho.lab.lab.Workload
```

```{rubric} Initialization
```

```{autodoc2-docstring} phospho.lab.lab.Workload.__init__
```

````{py:attribute} jobs
:canonical: phospho.lab.lab.Workload.jobs
:type: typing.List[phospho.lab.lab.Job]
:value: >
   None

```{autodoc2-docstring} phospho.lab.lab.Workload.jobs
```

````

````{py:attribute} _results
:canonical: phospho.lab.lab.Workload._results
:type: typing.Optional[typing.Dict[str, typing.Dict[str, phospho.lab.models.JobResult]]]
:value: >
   None

```{autodoc2-docstring} phospho.lab.lab.Workload._results
```

````

````{py:method} add_job(job: phospho.lab.lab.Job)
:canonical: phospho.lab.lab.Workload.add_job

```{autodoc2-docstring} phospho.lab.lab.Workload.add_job
```

````

````{py:method} from_config(config: dict) -> phospho.lab.lab.Workload
:canonical: phospho.lab.lab.Workload.from_config
:classmethod:

```{autodoc2-docstring} phospho.lab.lab.Workload.from_config
```

````

````{py:method} from_file(config_filename: str = 'phospho-config.yaml') -> phospho.lab.lab.Workload
:canonical: phospho.lab.lab.Workload.from_file
:classmethod:

```{autodoc2-docstring} phospho.lab.lab.Workload.from_file
```

````

````{py:method} async_run(messages: typing.Iterable[phospho.lab.models.Message], executor_type: typing.Literal[parallel, sequential] = 'parallel', max_parallelism: int = 10) -> typing.Dict[str, typing.Dict[str, phospho.lab.models.JobResult]]
:canonical: phospho.lab.lab.Workload.async_run
:async:

```{autodoc2-docstring} phospho.lab.lab.Workload.async_run
```

````

````{py:method} async_run_on_alternative_configurations(messages: typing.Iterable[phospho.lab.models.Message], executor_type: typing.Literal[parallel, sequential] = 'parallel') -> None
:canonical: phospho.lab.lab.Workload.async_run_on_alternative_configurations
:async:

```{autodoc2-docstring} phospho.lab.lab.Workload.async_run_on_alternative_configurations
```

````

````{py:method} optimize_jobs(accuracy_threshold: float = 1.0, min_count: int = 10) -> None
:canonical: phospho.lab.lab.Workload.optimize_jobs

```{autodoc2-docstring} phospho.lab.lab.Workload.optimize_jobs
```

````

````{py:method} __repr__()
:canonical: phospho.lab.lab.Workload.__repr__

````

````{py:property} results
:canonical: phospho.lab.lab.Workload.results
:type: typing.Optional[typing.Dict[str, typing.Dict[str, phospho.lab.models.JobResult]]]

```{autodoc2-docstring} phospho.lab.lab.Workload.results
```

````

````{py:method} results_df() -> typing.Any
:canonical: phospho.lab.lab.Workload.results_df

```{autodoc2-docstring} phospho.lab.lab.Workload.results_df
```

````

`````
