# {py:mod}`phospho.utils`

```{py:module} phospho.utils
```

```{autodoc2-docstring} phospho.utils
:allowtitles:
```

## Module Contents

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
* - {py:obj}`convert_to_jsonable_dict <phospho.utils.convert_to_jsonable_dict>`
  - ```{autodoc2-docstring} phospho.utils.convert_to_jsonable_dict
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

````{py:function} filter_nonjsonable_keys(arg_dict: dict) -> dict
:canonical: phospho.utils.filter_nonjsonable_keys

```{autodoc2-docstring} phospho.utils.filter_nonjsonable_keys
```
````

````{py:function} convert_to_jsonable_dict(arg_dict: dict, verbose: bool = False) -> typing.Dict[str, object]
:canonical: phospho.utils.convert_to_jsonable_dict

```{autodoc2-docstring} phospho.utils.convert_to_jsonable_dict
```
````
