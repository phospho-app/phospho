# Contribution guide

We welcome contributions from every respectful contributor!

There are multiple ways you can contribute to phospho:

- Help us address bugs and new features by opening an [Issue on Github](https://github.com/phospho-app/phospho/issues)
- Reach out by [mail](mailto:contact@phospho.ai?subject=[GitHub]%20Contribution)
- Engage in the community on [Discord](https://discord.gg/MXqBJ9pBsx)
- Enhance the phospho package by adding new evaluation jobs to the `job_library`

This guide will focus on how to add jobs to the phospho library.

## Setup

### Requirements

- Python 3.9 or higher
- [Poetry](https://python-poetry.org/) for packaging and dependency management

Install poetry and the phospho project:

```bash
curl -sSL https://install.python-poetry.org | python3 -
cd phospho-python
poetry install
```

### Guide: How to create a job?

Create a new job in `phospho-python/lab/job_library.py` by taking an existing job as an example.

```python
# A Job is a function that takes as first parameter a Message and that returns a JobResult
# Additional parameters can be specified

def prompt_to_bool(
    message: Message,
    prompt: str,
    format_kwargs: Optional[dict] = None,
    model: str = "gpt-3.5-turbo",
) -> JobResult:
    """
    Runs a prompt on a message and returns a boolean result.
    """

    # Call any LLM models or API in the job
    openai_model = OpenAIModel(config.OPENAI_API_KEY, model)
    if format_kwargs is None:
        format_kwargs = {}
    formated_prompt = prompt.format(
        message_content=message.content,
        message_context=message.previous_messages_transcript(with_role=True),
        **format_kwargs,
    )
    llm_response = openai_model.invoke(formated_prompt).strip()
    if llm_response is None:
        bool_response = False
    else:
        bool_response = llm_response.lower() == "true"

    # Return a JobResult
    return JobResult(
        job_id="prompt_to_bool",
        result_type=ResultType.bool,
        value=bool_response,
        logs=[formated_prompt, llm_response],
    )
```

Using this framework will allow the job to be compatible with the `.optimize` method (to figure out the best set of parameters) and the exported results (to store the analytics in a standard way).

### Testing

We use [pytest](https://docs.pytest.org/en/stable/) for testing. Test files are located in the `phospho-python/tests` folder. To run the tests, use the following command:

```bash
poetry run pytest
```

### Building locally

To build the package locally, run :

```bash
poetry build
```

You can then import the built package (even in a different project and environment) using (replace with the path to the actual file) :

```bash
pip install path/to/dist/phospho-0.1.0.tar.gz
```

You can also test your dockerfiles locally by running

```bash
docker build -t <name ie frontend, backend, etc...> .
```

or

```bash
docker build --file <./filename> -t <name ie frontend, backend, etc...> .
```

## Running temporal locally

```bash
temporal server start-dev --db-filename your_temporal.db --ui-port 8080
```

## Pull Requests

In github, create a Pull Request targeting the `dev` branch.

### Publishing

Publishing is handled by Github Actions when maintainers create a new release.

1. Create a new Release in Github. As a tag, use the same version as in `pyproject.toml`
2. Tick the pre-release box to deploy to test pypi. Don't tick it to deploy to the main pypi.
