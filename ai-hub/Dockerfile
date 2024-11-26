FROM python:3.11

# Steps are cached with Kaniko in GCP Artifcat registry
# The cache is kept 72 hours (see cloudbuild.yaml)

WORKDIR /src
RUN pip install poetry

# Copy pyproject.toml and poetry.lock
COPY ./pyproject.toml /src/pyproject.toml
COPY ./poetry.lock /src/poetry.lock

# Clone the phospho_backend repository directly
RUN apt-get update && apt-get install -y git && \
    git clone --recursive https://github.com/phospho-app/phospho.git /src/phospho_backend && \
    rm -rf /var/lib/apt/lists/*


# Install dependencies
RUN poetry config virtualenvs.in-project true
RUN poetry install --no-interaction --no-ansi

# Install dependencies
RUN poetry install --no-interaction --no-ansi

# Copy source code
COPY ./app /src/app
COPY ./main.py /src/main.py

EXPOSE 8080

# Run the worker
CMD ["poetry", "run", "python", "main.py"]
