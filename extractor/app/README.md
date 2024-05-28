# phospho extractor

This is the extractor service for the phospho project. It is responsible for extracting the requried data from tasks and sessions :

- evaluations
- events
- topics

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

## Running the server

> Make sure to use the right port, so you can have 2 servers running at the same time.

```bash
poetry run uvicorn app.main:app --reload --port 7605
```

## Security

Requests to this server are considered already authenticated and authorized. This is because the server is behind our phospho backend. A secret key (`EXTRACTOR_SECRET_KEY`) for the FastAPI app, any request will be rejected if the secret key is not provided in the request headers.
