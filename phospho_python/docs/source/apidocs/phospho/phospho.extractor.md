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
* - {py:obj}`detect_usage_from_input_output <phospho.extractor.detect_usage_from_input_output>`
  - ```{autodoc2-docstring} phospho.extractor.detect_usage_from_input_output
    :summary:
    ```
* - {py:obj}`detect_model_from_input_output <phospho.extractor.detect_model_from_input_output>`
  - ```{autodoc2-docstring} phospho.extractor.detect_model_from_input_output
    :summary:
    ```
* - {py:obj}`extract_data_from_output <phospho.extractor.extract_data_from_output>`
  - ```{autodoc2-docstring} phospho.extractor.extract_data_from_output
    :summary:
    ```
* - {py:obj}`extract_data_from_input <phospho.extractor.extract_data_from_input>`
  - ```{autodoc2-docstring} phospho.extractor.extract_data_from_input
    :summary:
    ```
* - {py:obj}`extract_metadata_from_input_output <phospho.extractor.extract_metadata_from_input_output>`
  - ```{autodoc2-docstring} phospho.extractor.extract_metadata_from_input_output
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

````{py:function} detect_usage_from_input_output(input: typing.Any, output: typing.Any) -> typing.Optional[typing.Dict[str, float]]
:canonical: phospho.extractor.detect_usage_from_input_output

```{autodoc2-docstring} phospho.extractor.detect_usage_from_input_output
```
````

````{py:function} detect_model_from_input_output(input: typing.Any, output: typing.Any) -> typing.Optional[str]
:canonical: phospho.extractor.detect_model_from_input_output

```{autodoc2-docstring} phospho.extractor.detect_model_from_input_output
```
````

````{py:function} extract_data_from_output(output: typing.Optional[typing.Union[phospho.extractor.RawDataType, str]] = None, raw_output: typing.Optional[phospho.extractor.RawDataType] = None, output_to_str_function: typing.Optional[typing.Callable[[typing.Any], str]] = None) -> typing.Tuple[typing.Optional[str], typing.Optional[typing.Union[typing.Dict[str, object], str]]]
:canonical: phospho.extractor.extract_data_from_output

```{autodoc2-docstring} phospho.extractor.extract_data_from_output
```
````

````{py:function} extract_data_from_input(input: typing.Union[phospho.extractor.RawDataType, str], raw_input: typing.Optional[phospho.extractor.RawDataType] = None, input_to_str_function: typing.Optional[typing.Callable[[typing.Any], str]] = None) -> typing.Tuple[str, typing.Optional[typing.Union[typing.Dict[str, object], str]]]
:canonical: phospho.extractor.extract_data_from_input

```{autodoc2-docstring} phospho.extractor.extract_data_from_input
```
````

````{py:function} extract_metadata_from_input_output(input: typing.Union[phospho.extractor.RawDataType, str], output: typing.Optional[typing.Union[phospho.extractor.RawDataType, str]] = None, input_output_to_usage_function: typing.Optional[typing.Callable[[typing.Any, typing.Any], typing.Dict[str, float]]] = None) -> typing.Dict[str, object]
:canonical: phospho.extractor.extract_metadata_from_input_output

```{autodoc2-docstring} phospho.extractor.extract_metadata_from_input_output
```
````
