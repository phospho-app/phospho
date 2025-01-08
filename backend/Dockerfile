FROM python:3.11

# Steps are cached with Kaniko in GCP Artifcat registry
# The cache is kept 72 hours (see cloudbuild.yaml)

WORKDIR /src
RUN pip install poetry

# Copy pyproject.toml and poetry.lock
COPY ./backend/pyproject.toml /src/pyproject.toml
COPY ./backend/README.md /src/README.md
COPY ./backend/poetry.lock /src/poetry.lock

RUN poetry config virtualenvs.create false

# Copy source code
COPY ./backend/phospho_backend /src/phospho_backend
# Copy phospho package
COPY ./phospho-python /phospho-python
RUN poetry install --no-interaction --no-ansi



# Run the server on port 80
CMD ["uvicorn", "phospho_backend.main:app", "--host", "0.0.0.0", "--port", "80"]