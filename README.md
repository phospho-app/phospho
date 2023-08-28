# phospho

This is the repo of the phospho package.

## Requirements

- Python 3.8 or higher
- [Poetry](https://python-poetry.org/) for packaging and dependency management

## Installation

Install poetry
    
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

You can check the installed version with :

```bash
poetry --version
```

Poetry will automatically create a virtual environment for you. To install the dependencies, run

```bash
poetry install
```

## Testing
We use [pytest](https://docs.pytest.org/en/stable/) for testing. Test files are located in the `tests` folder. To run the tests, use the following command:
    
```bash
poetry run pytest
```

## Building locally 
To build the package locally, run :

```bash
poetry build
```

You can then import the built package (even in a different project and environment) using (replace with the path to the actual file) :

```bash
pip install path/to/dist/phospho-0.1.0.tar.gz
```

## Publishing
DO NOT PUBLISH YET