FROM python:3.11

# Steps are cached with Kaniko in GCP Artifcat registry
# The cache is kept 72 hours (see cloudbuild.yaml)

WORKDIR /src
RUN pip install poetry

# Copy pyproject.toml and poetry.lock
COPY ./pyproject.toml /src/pyproject.toml
COPY ./poetry.lock /src/poetry.lock

# Install dependencies
RUN poetry config virtualenvs.create false && poetry install --no-interaction --no-ansi

# Copy phospho package
COPY ./phospho-python /phospho-python
RUN poetry install --with dev --no-interaction --no-ansi

# Copy source code
COPY ./app /src/app

# Run the server on port 80
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "80"]