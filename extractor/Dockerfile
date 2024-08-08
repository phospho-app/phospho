FROM python:3.11

# Steps are cached with Kaniko in GCP Artifcat registry
# The cache is kept 72 hours (see cloudbuild.yaml)

WORKDIR /src
RUN pip install poetry

# Copy pyproject.toml and poetry.lock
COPY ./pyproject.toml /src/pyproject.toml
COPY ./poetry.lock /src/poetry.lock


# Create virtualenv at .venv in the project instead of ~/.cache/
RUN poetry config virtualenvs.in-project true

# Install dependencies
RUN poetry install --no-interaction --no-ansi

# Copy phospho package
COPY ./phospho-python /phospho-python
RUN poetry install --with dev --no-interaction --no-ansi

# Copy source code
COPY ./app /src/app
COPY ./main.py /src/main.py

EXPOSE 7605

# So GCP can send probe
ENV HOSTNAME="0.0.0.0" 


# Run the worker
CMD ["poetry", "run", "python", "main.py"]
