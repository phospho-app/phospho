# phospho extractor

This is the extractor service for the phospho project. It is responsible for extracting the required data points from tasks and sessions.

## Instalation

This project use Poetry.

Create a `.env` file with the following content:

```bash
ENVIRONMENT="test"
EXTRACTOR_SECRET_KEY=""
MONGODB_NAME="test"
MONGODB_URL=""
COHERE_API_KEY=""
OPENAI_API_KEY=""
TEST_PROPELAUTH_ORG_ID=""
GCP_JSON_CREDENTIALS='{}'
```

Install the dependencies if you are running loccaly in dev mode:

```bash
poetry install --with dev
```

# Running the server

```bash
poetry run uvicorn app.main:app --reload --port 8001
```

## Security

Requests to this server are considered already authenticated and authorized. This is because the server is behind our phospho backend. Any request will be rejected if the secret key is not provided in the request headers.
