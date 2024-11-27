# Deploying the Phospho Platform with Docker

Welcome! This guide will help you deploy the Phospho Platform using Docker Compose. Phospho is an advanced backoffice for managing your LLM apps, with tools like clustering, data labeling, and user analytics. This deployment guide is designed to provide easy-to-follow steps, allowing you to set up Phospho locally or on your server.

## Prerequisites

### 1. **Create a Propelauth Account**

Propelauth is essential for authentication and security within your application.

- **Sign Up:** [Create your Propelauth account](https://propelauth.com/signup)

### 2. **Obtain an OpenAI API Key**

An OpenAI API Key is required to integrate OpenAI services into your platform.

- **Get API Key:** [Register and obtain your OpenAI API Key](https://platform.openai.com/account/api-keys)

### 3. **Register for MongoDB**

MongoDB will serve as your database solution.

- **Sign Up:** [Register for MongoDB](https://www.mongodb.com/try)

### 4. **Install Docker**

Docker is used to containerize your application, ensuring consistency across different environments.

- **Install Docker:** [official Docker installation guide](https://docs.docker.com/get-docker/).

### 5. **Set up Google Cloud Platform (GCP)**

GCP is used for cloud compuations of some metrics.

- **Get Started with GCP:** [Deploy on Google Cloud Platform](https://cloud.google.com/docs/get-started?hl=fr)

## Step 1: Set Up Your Project Directory

First, clone the repository containing the source code of the platform with

```bash
git clone https://github.com/phospho-app/phospho.git
```

## Step 2: Set up your environment files

First create in the root folder a file called `.env.docker` following this example:

```bash
# Application Environment
APP_ENV=local
ENVIRONMENT="test"

# API Configuration
API_VERSION=v0
NEXT_PUBLIC_API_VERSION=v0
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
LOCAL_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_LOCAL_API_URL=http://127.0.0.1:8000

# Authentication Settings
NEXT_PUBLIC_AUTH_URL=https://<your_id>.propelauthtest.com
PROPELAUTH_API_KEY=
PROPELAUTH_REDIRECT_URI=http://localhost:3000/api/auth/callback
PROPELAUTH_VERIFIER_KEY=-----BEGIN PUBLIC KEY-----
PROPELAUTH_URL="https://<your_id>.propelauthtest.com"

# GCP Configuration
GCP_PROJECT_ID=""
GCP_SERVICEACCOUNT_EMAIL=
GCP_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----
GCP_JSON_CREDENTIALS_NATURAL_LANGUAGE_PROCESSING=
GCP_JSON_CREDENTIALS_BUCKET=

# OPENAI API Key For Chat and Embedding models
OPENAI_API_KEY=
OPENAI_BASE_URL=
# MongoDB Database Configuration
MONGODB_NAME="test"
MONGODB_URL=""

# Local Development Settings
TEMPORAL_HOST_URL=host.docker.internal:7233
TEMPORAL_NAMESPACE=default
TEMPORAL_MTLS_TLS_CERT_BASE64=
TEMPORAL_MTLS_TLS_KEY_BASE64=

# (OPTIONNAL) Services and Integrations
RESEND_API_KEY=
STRIPE_SECRET_KEY=
STRIPE_WEBHOOK_SECRET=
SENTRY_DSN=
EXTRACTOR_SENTRY_DSN=
SLACK_URL=
AZURE_OPENAI_KEY=
AZURE_OPENAI_ENDPOINT=
TEST_PROPELAUTH_ORG_ID=
TEST_PROPELAUTH_USER_ID=

```

Make sure to replace the placeholders with your actual credentials. These environment variables are essential for connecting the different components of the Phospho platform.
Please put this .env file in the `platform`, `ai-hub` and `backend`folder

## Step 3: Build and run

### Temporal

Make sure Temporal is running. Use the [Temporal CLI](https://temporal.io/setup/install-temporal-cli) to do so.

```bash
temporal server start-dev --db-filename your_temporal.db --ui-port 7999
```

For production environment, we recommend you use the Cloud version of Temporal. If so, make sure to update the env variables starting with `TEMPORAL_`.

### Docker compose

```bash
docker compose up
```

## Conclusion

Congratulations! You have successfully deployed the Phospho platform with Docker. You can now start exploring the platform and use its powerful tools to manage your LLM apps more effectively.

If you run into any issues, feel free to ask for support on the [Phospho Discord channel](https://discord.gg/phospho).
