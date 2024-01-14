# {py:mod}`phospho.utils`

```{py:module} phospho.utils
```

```{autodoc2-docstring} phospho.utils
:allowtitles:
```

## Module Contents

### Classes

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`MutableGenerator <phospho.utils.MutableGenerator>`
  - ```{autodoc2-docstring} phospho.utils.MutableGenerator
    :summary:
    ```
* - {py:obj}`MutableAsyncGenerator <phospho.utils.MutableAsyncGenerator>`
  - ```{autodoc2-docstring} phospho.utils.MutableAsyncGenerator
    :summary:
    ```
````

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`generate_timestamp <phospho.utils.generate_timestamp>`
  - ```{autodoc2-docstring} phospho.utils.generate_timestamp
    :summary:
    ```
* - {py:obj}`generate_uuid <phospho.utils.generate_uuid>`
  - ```{autodoc2-docstring} phospho.utils.generate_uuid
    :summary:
    ```
* - {py:obj}`is_jsonable <phospho.utils.is_jsonable>`
  - ```{autodoc2-docstring} phospho.utils.is_jsonable
    :summary:
    ```
* - {py:obj}`filter_nonjsonable_keys <phospho.utils.filter_nonjsonable_keys>`
  - ```{autodoc2-docstring} phospho.utils.filter_nonjsonable_keys
    :summary:
    ```
* - {py:obj}`convert_content_to_loggable_content <phospho.utils.convert_content_to_loggable_content>`
  - ```{autodoc2-docstring} phospho.utils.convert_content_to_loggable_content
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`logger <phospho.utils.logger>`
  - ```{autodoc2-docstring} phospho.utils.logger
    :summary:
    ```
````

### API

````{py:data} logger
:canonical: phospho.utils.logger
:value: >
   'getLogger(...)'

```{autodoc2-docstring} phospho.utils.logger
```

````

````{py:function} generate_timestamp() -> int
:canonical: phospho.utils.generate_timestamp

```{autodoc2-docstring} phospho.utils.generate_timestamp
```
````

````{py:function} generate_uuid() -> str
:canonical: phospho.utils.generate_uuid

```{autodoc2-docstring} phospho.utils.generate_uuid
```
````

````{py:function} is_jsonable(x: typing.Any) -> bool
:canonical: phospho.utils.is_jsonable

```{autodoc2-docstring} phospho.utils.is_jsonable
```
````

````{py:function} filter_nonjsonable_keys(arg_dict: dict, verbose: bool = False) -> typing.Dict[str, object]
:canonical: phospho.utils.filter_nonjsonable_keys

```{autodoc2-docstring} phospho.utils.filter_nonjsonable_keys
```
````

````{py:function} convert_content_to_loggable_content(content: typing.Any) -> typing.Union[typing.Dict[str, object], str, None]
:canonical: phospho.utils.convert_content_to_loggable_content

```{autodoc2-docstring} phospho.utils.convert_content_to_loggable_content
```
````

`````{py:class} MutableGenerator(generator: typing.Generator, stop: typing.Callable[[typing.Any], bool])
:canonical: phospho.utils.MutableGenerator

```{autodoc2-docstring} phospho.utils.MutableGenerator
```

```{rubric} Initialization
```

```{autodoc2-docstring} phospho.utils.MutableGenerator.__init__
```

````{py:method} __iter__()
:canonical: phospho.utils.MutableGenerator.__iter__

```{autodoc2-docstring} phospho.utils.MutableGenerator.__iter__
```

````

````{py:method} __next__()
:canonical: phospho.utils.MutableGenerator.__next__

```{autodoc2-docstring} phospho.utils.MutableGenerator.__next__
```

````

`````

`````{py:class} MutableAsyncGenerator(generator: typing.AsyncGenerator, stop: typing.Callable[[typing.Any], bool])
:canonical: phospho.utils.MutableAsyncGenerator

```{autodoc2-docstring} phospho.utils.MutableAsyncGenerator
```

```{rubric} Initialization
```

```{autodoc2-docstring} phospho.utils.MutableAsyncGenerator.__init__
```

````{py:method} __aiter__()
:canonical: phospho.utils.MutableAsyncGenerator.__aiter__

```{autodoc2-docstring} phospho.utils.MutableAsyncGenerator.__aiter__
```

````

````{py:method} __anext__()
:canonical: phospho.utils.MutableAsyncGenerator.__anext__
:async:

```{autodoc2-docstring} phospho.utils.MutableAsyncGenerator.__anext__
```

````

`````
