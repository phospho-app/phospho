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

To generate new certificates, we recommend you use tcld: https://learn.temporal.io/getting_started/python/run_workers_with_cloud_python/

Follow these lines

```bash
tcld gen ca --org "your-organisation" -d 365d --ca-cert ca.pem --ca-key ca.key
tcld gen leaf --org "your-organsation" -d 364d --ca-cert ca.pem --ca-key ca.key --cert client.pem --key client.key
openssl x509 -in ca.pem -text -noout
```

You then have to encrypt the client key and client certificate in base 64 like so, using openssl

```bash
openssl base64 -in client.pem -out client-base64-pem
openssl base64 -in client.key -out client-base64-key
```

# Running the worker

```bash
poetry run python main.py
```

**Warning:** You have to put your EXTRACTOR_SECRET_KEY in your backend .env.

## Security

Requests to this server are considered already authenticated and authorized. This is because the server is behind our phospho backend. Any request will be rejected if the secret key is not provided in the request headers.
