# ai-hub

The dedicated service handling proprietary AI related tasks (training and inference).

## Installation

Be sure you run the following command in a terminal located in this ai-hub folder.

### Prerequisites

You need [poetry](https://python-poetry.org/) to install the dependencies and manage your environment.

### Install dependencies

Be sure your virtual environment is activated. Install python depedencies with:

```bash
poetry install
```

### Setup env variables

Create a `.env` file in this `ai-hub` folder and add the following variables:

```bash
ENVIRONMENT="test" # Or "production"
MONGODB_NAME=""
MONGODB_URL=""

OPENAI_API_KEY=""
ANYSCALE_API_KEY=""

# For local
TEMPORAL_HOST_URL=localhost:7233
TEMPORAL_NAMESPACE=default
```

## Running the worker locally

You first need to install temporal locally to create a local workflow queue. On MacOS, you can just run:

```bash
brew install temporal
```

For other platform, look at the [Temporal docs.](https://temporal.io/setup/install-temporal-cli)

Once installed just run the following command to run your local queue
Don't forget to edit your .env configuration, these are the default parameters. Look at the actual port that is displayed when running temporal.

```text .env
TEMPORAL_HOST_URL=localhost:7233
TEMPORAL_NAMESPACE=default
```

```bash
temporal server start-dev --db-filename your_temporal.db --ui-port 8080
```

You can now run the worker in a second terminal with

```bash
poetry run python main.py
```

## Endpoint URL

In test, the service will be available at `?`.
In staging, the service will be available at `https://phospho-proprietary-ai-hub-staging-zxs3h5fuba-ew.a.run.app`.
In production, the service will be available at `https://phospho-proprietary-ai-hub-zxs3h5fuba-ew.a.run.app`.

## Submodule update

```bash
git submodule init
git submodule update --init --recursive
```
