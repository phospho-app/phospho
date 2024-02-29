# Guide

## How to run github actions locally?

This is great to debug workflows before pushing them to main.

### Setup

Install [act](https://github.com/nektos/act)

```bash
brew install act
```

Install [Docker](https://www.docker.com/get-started/)

### Execution

To run the `test_back` workflow locally:

```bash
# Must be in the root folder
cd monorepo
act -j test_back --secret-file backend/.env --var-file backend/.env --container-architecture linux/amd64
```
