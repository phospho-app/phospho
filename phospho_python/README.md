# phospho Python Client

Phospho is an open source platform to help you monitor LLM apps.

With phospho, monitor every user interaction with your LLM app to identify issues and improve performance. Understand how users use your app and which versions of your product are the most successful.

Read the docs at [docs.phospho.ai](https://docs.phospho.ai/).

> _Warning_ : This project is still under active development!

## Installation of the phospho client

You need Python `>=3.9`

```bash
pip install --upgrade phospho
```

## Quickstart

Create an account on [phospho](https://platform.phospho.ai/). Create an API key and note down the project id. Set them as environment variables:

```bash
export PHOSPHO_API_KEY="your-api-key"
export PHOSPHO_PROJECT_ID="project-id"
```

In the code of your LLM app, log interactions with your agent using `phospho.log()`.

```python
import phospho

phospho.init()

# This is how you log interactions to phospho as strings
phospho.log(input="The user input", output="Your LLM app output")

```

You can also directly pass OpenAI API query and responses (or any object with same format) to phospho :

```python
import phospho
import openai

phospho.init()
openai_client = openai.OpenAI()

# This is your agent code
query = {
    "messages": [{"role": "user", "content": "The user input"}],
    "model": "gpt-3.5-turbo",
}
response = openai_client.chat.completions.create(**query)

# Log the interactions to phospho
phospho.log(input=query, output=response)
```

Monitor and visualize your agent on the [phospho dashboard](https://platform.phospho.ai/).

## phospho lab

You can also use phospho locally to run evaluations and event detection on your text messages.
See the [phospho lab documentation](https://docs.phospho.ai/local/phospho-lab) for more information or the notebook `quicksart.ipynb` in the `notebooks` folder.

## Usage

Read the docs at [docs.phospho.ai](https://docs.phospho.ai/) for more information.
Use your phospho dashboard to monitor your agent, score interactions and detect events.
