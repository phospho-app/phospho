# phospho backend

## Local install and setup

This project uses Poetry and Python 3.11.

Be sure you run the following in your terminal located in the backend folder.
Start by installing python dependencies with:

```bash
# 1 - install poetry
pip install poetry
# 2 - install backend dependancies
poetry install
```

Create a .env file and fill the necessary information following this example:

### Environment file

```bash
ENVIRONMENT="test"

# Services
RESEND_API_KEY=
OPENAI_API_KEY=
SENTRY_DSN=

# Database
MONGODB_NAME="test"
MONGODB_URL="mongodb+srv://..." # Look in MongoDB atlas

# Slack webhook
SLACK_URL= # Look in Slack admin

# GCP
GCP_PROJECT_ID="portal-385519"
GCP_JSON_CREDENTIALS=

# Auth
PROPELAUTH_URL="https://80082208909.propelauthtest.com"
PROPELAUTH_API_KEY=

# For testing. You can replace this by any user from the Propelauth TEST env
TEST_PROPELAUTH_ORG_ID="f63c18ff-7fad-4436-8bf4-8a336a596d94"
TEST_PROPELAUTH_USER_ID="65bd900c-cb79-4bd8-a278-5ea5f2a0f362"
PHOSPHO_API_KEY=

# For access to phospho models
PHOSPHO_AI_HUB_URL=""
PHOSPHO_AI_HUB_API_KEY=""

# For the chat completion endpoint
AZURE_OPENAI_KEY=""
AZURE_OPENAI_ENDPOINT=""
```

### Run backend server

Now you can run the backend server through this command:

```
poetry run uvicorn phospho_backend.main:app --reload
```

### (Optionnal) Run tests

1. Make sure you have setup your environment variables. To load the .env files:

   ```
   set -o allexport; source .env; set +o allexport
   ```

2. Start the local server in test mode :

   ```bash
   poetry run uvicorn phospho_backend.main:app --reload
   ```

3. Run tests through poetry

   ```bash
   poetry run pytest
   ```

## Services to set up

### Install MongoDB local

We use MongoDB Atlas to host the database in the cloud.

However, if you want to experiment more, you can setup MongoDB on your own computer. [Install MongoDB locally to have your own local database.](https://www.mongodb.com/docs/manual/tutorial/install-mongodb-on-os-x/)

```bash
brew tap mongodb/brew
brew update
brew install mongodb-community@7.0
```

Add the MongoDB as a backend service

```bash
brew services start mongodb-community@7.0
```

Disable telemetry for privacy reasons

```bash
mongosh
disableTelemetry()
```

When running `mongosh`, you'll see a URL. Note it down.

```text
Connecting to:		mongodb://127.0.0.1:27017/?directConnection=true&serverSelectionTimeoutMS=2000&appName=mongosh+2.1.1
Using MongoDB:		7.0.2
Using Mongosh:		2.1.1
```

In the Python backend, we use the async client [Motor](https://motor.readthedocs.io/en/stable/tutorial-asyncio.html). Async lets the backend do stuff while it's waiting for the db response.

In tests and other scripts, you can use [Pymongo](https://pymongo.readthedocs.io/en/stable/tutorial.html). It is synchronous and installed when you install Motor. It's useful when you need to wait for the response anyways.

## Deployment

This app is packaged in a Docker container and is deployed with github actions.

- The step by step is available in the [github workflow backend-deploy](../.github/workflows/backend-deploy.yml)
- Build step are executed in GCP with [cloud build](https://cloud.google.com/sdk/gcloud/reference/builds/submit)
- Tool for building: [Kaniko](https://github.com/GoogleContainerTools/kaniko). This is useful for caching. See [cloudbuild.yaml](./cloudbuild.yaml) for configuration.
- Tool for the build steps: Docker. See the [Dockerfile](./Dockerfile) for how the execution environment is packaged.

## Stripe

To get stripe working on your local development server, you need to setup the stripe webhook locally, for that, run the following command and update your stripe-webhook-secret

```rb
stripe listen --forward-to localhost:8000/api/organizations/stripe-webhook
```

### Populate the local test database

Run :

```
python scripts/populate_local_db.py
```

You will be prompted for your API key and project id (TEST env of propelAuth)

## To decide

At which level do we handle the try excepts? Service level? db level?
Timestamp format? Typing (str or int)?

## Common issues

Pydantic models make the app crash if a field value is None and the field is not Optional.
