FROM python:3.11

# Steps are cached with Kaniko in GCP Artifcat registry
# The cache is kept 72 hours (see cloudbuild.yaml)

WORKDIR /src
RUN pip install poetry

# Copy pyproject.toml and poetry.lock
COPY ./ai-hub/pyproject.toml /src/pyproject.toml
COPY ./ai-hub/poetry.lock /src/poetry.lock

COPY ./phospho-python/ /phospho-python
COPY ./backend/ /backend

# Install dependencies
RUN poetry config virtualenvs.in-project true
RUN poetry install --no-interaction --no-ansi

# Copy source code
COPY ./ai-hub/ai_hub /src/ai_hub
COPY ./ai-hub/main.py /src/main.py

EXPOSE 8081

# Run the worker
CMD ["poetry", "run", "python", "main.py"]
