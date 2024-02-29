# vLLM documents

## Build the docs

```bash
# Install docs dependencies with poetry
poetry install --with docs

# Build the docs
cd docs
make clean
make html
```

## Open the docs with your browser

```bash
python -m http.server -d build/html/
```

Launch your browser and open localhost:8000.
