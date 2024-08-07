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
OPENAI_API_KEY=""
TEST_PROPELAUTH_ORG_ID=""
GCP_JSON_CREDENTIALS='{}'
```

Install the dependencies if you are running loccaly in dev mode:

```bash
poetry install --with dev
```

## Generating New Certificates

To generate new certificates, we recommend you use certstrap: https://learn.temporal.io/getting_started/python/run_workers_with_cloud_python/

You can install it in three easy steps

```bash
$ git clone https://github.com/square/certstrap
$ cd certstrap
$ go build
```

You can now create a certificate authority and use this certificate for the namespace.
Just run

```bash
./certstrap init --common-name "phospho-example-namespace"
```

This will generate a .crt, this is the certificate we need to upload to temporal
You will also generate a .key which is PRIVATE, do not share this key, it is needed on the client to connect to temporal

# Running the server

```bash
poetry run uvicorn app.main:app --reload --port 7605
```

**Warning:** You have to put your EXTRACTOR_SECRET_KEY in your backend .env.

## Security

Requests to this server are considered already authenticated and authorized. This is because the server is behind our phospho backend. Any request will be rejected if the secret key is not provided in the request headers.
