# phospho extractor

The extractor is a temporal worker that runs long and tedious workflows.
A worker is composed of activities.

## Installation

```bash
poetry install
```

Edit the `.env` file to set the environment variables.

```bash
ENVIRONMENT="test"
EXTRACTOR_SECRET_KEY=""
```

## Adding dependancies

```bash
poetry add <module-name>
```

## Running the worker

> To run the worker simply run main.py

```bash
python3.11 app/main.py
```
