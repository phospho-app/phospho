# {py:mod}`phospho.extractor`

```{py:module} phospho.extractor
```

```{autodoc2-docstring} phospho.extractor
:allowtitles:
```

## Module Contents

### Functions

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`convert_to_dict <phospho.extractor.convert_to_dict>`
  - ```{autodoc2-docstring} phospho.extractor.convert_to_dict
    :summary:
    ```
* - {py:obj}`detect_str_from_input <phospho.extractor.detect_str_from_input>`
  - ```{autodoc2-docstring} phospho.extractor.detect_str_from_input
    :summary:
    ```
* - {py:obj}`detect_str_from_output <phospho.extractor.detect_str_from_output>`
  - ```{autodoc2-docstring} phospho.extractor.detect_str_from_output
    :summary:
    ```
* - {py:obj}`get_input_output <phospho.extractor.get_input_output>`
  - ```{autodoc2-docstring} phospho.extractor.get_input_output
    :summary:
    ```
````

### Data

````{list-table}
:class: autosummary longtable
:align: left

* - {py:obj}`RawDataType <phospho.extractor.RawDataType>`
  - ```{autodoc2-docstring} phospho.extractor.RawDataType
    :summary:
    ```
* - {py:obj}`logger <phospho.extractor.logger>`
  - ```{autodoc2-docstring} phospho.extractor.logger
    :summary:
    ```
````

### API

````{py:data} RawDataType
:canonical: phospho.extractor.RawDataType
:value: >
   None

```{autodoc2-docstring} phospho.extractor.RawDataType
```

````

````{py:data} logger
:canonical: phospho.extractor.logger
:value: >
   'getLogger(...)'

```{autodoc2-docstring} phospho.extractor.logger
```

````

````{py:function} convert_to_dict(x: typing.Any) -> typing.Dict[str, object]
:canonical: phospho.extractor.convert_to_dict

```{autodoc2-docstring} phospho.extractor.convert_to_dict
```
````

````{py:function} detect_str_from_input(input: phospho.extractor.RawDataType) -> str
:canonical: phospho.extractor.detect_str_from_input

```{autodoc2-docstring} phospho.extractor.detect_str_from_input
```
````

````{py:function} detect_str_from_output(output: phospho.extractor.RawDataType) -> str
:canonical: phospho.extractor.detect_str_from_output

```{autodoc2-docstring} phospho.extractor.detect_str_from_output
```
````

````{py:function} get_input_output(input: typing.Union[phospho.extractor.RawDataType, str], output: typing.Optional[typing.Union[phospho.extractor.RawDataType, str]] = None, raw_input: typing.Optional[phospho.extractor.RawDataType] = None, raw_output: typing.Optional[phospho.extractor.RawDataType] = None, input_to_str_function: typing.Optional[typing.Callable[[typing.Any], str]] = None, output_to_str_function: typing.Optional[typing.Callable[[typing.Any], str]] = None) -> typing.Tuple[str, typing.Optional[str], typing.Optional[typing.Union[typing.Dict[str, object], str]], typing.Optional[typing.Union[typing.Dict[str, object], str]]]
:canonical: phospho.extractor.get_input_output

```{autodoc2-docstring} phospho.extractor.get_input_output
```
````
