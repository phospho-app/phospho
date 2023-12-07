# Contribution guide

This is the repo of the phospho package.

## Requirements

This repo use Poetry.

- Python 3.8 or higher
- [Poetry](https://python-poetry.org/) for packaging and dependency management

### Installation

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

### Testing
We use [pytest](https://docs.pytest.org/en/stable/) for testing. Test files are located in the `tests` folder. To run the tests, use the following command:
    
```bash
poetry run pytest
```

### Building locally 
To build the package locally, run :

```bash
poetry build
```

You can then import the built package (even in a different project and environment) using (replace with the path to the actual file) :

```bash
pip install path/to/dist/phospho-0.1.0.tar.gz
```

## Pull Requests

In github, create a Pull Request targeting the `dev` branch.

###  Publishing

Publishing is handled by Github Actions when maintainers create a new release.

1. Create a new Release in Github. As a tag, use the same version as in `pyproject.toml`
2. Tick the pre-release box to deploy to test pypi. Don't tick it to deploy to the main pypi. 