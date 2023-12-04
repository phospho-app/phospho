# {py:mod}`phospho.consumer`

```{py:module} phospho.consumer
```

```{autodoc2-docstring} phospho.consumer
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`Consumer <phospho.consumer.Consumer>`
  - ```{autodoc2-docstring} phospho.consumer.Consumer
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`logger <phospho.consumer.logger>`
  - ```{autodoc2-docstring} phospho.consumer.logger
    :summary:
    ```
````

### API

````{py:data} logger
:canonical: phospho.consumer.logger
:value: >
   'getLogger(...)'

```{autodoc2-docstring} phospho.consumer.logger
```

````

`````{py:class} Consumer(log_queue: phospho.log_queue.LogQueue, client: phospho.client.Client, tick: float = 0.5)
:canonical: phospho.consumer.Consumer

Bases: {py:obj}`threading.Thread`

```{autodoc2-docstring} phospho.consumer.Consumer
```

```{rubric} Initialization
```

```{autodoc2-docstring} phospho.consumer.Consumer.__init__
```

````{py:method} run() -> None
:canonical: phospho.consumer.Consumer.run

````

````{py:method} send_batch() -> None
:canonical: phospho.consumer.Consumer.send_batch

```{autodoc2-docstring} phospho.consumer.Consumer.send_batch
```

````

````{py:method} stop()
:canonical: phospho.consumer.Consumer.stop

```{autodoc2-docstring} phospho.consumer.Consumer.stop
```

````

`````
