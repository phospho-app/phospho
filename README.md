# phospho Python Client

With phospho, you can monitor every user interaction with your LLM app to identify issues and improve performance. Understand how users use your app and which versions of your product are the most successful.

Read the docs at [docs.phospho.app](https://docs.phospho.app/).

> *Warning* : This project is still under active development!

## Installation of the phospho client

You need Python `>=3.8`

```bash
pip install --upgrade phospho
```

## Quickstart

Create a phospho account and go to the [phospho dashboard](https://platform.phospho.app/). Create a project. In your project settings, create an API key. Set them as environment variables:

```bash
export PHOSPHO_PROJECT_ID="project-id"
export PHOSPHO_API_KEY="your-api-key"
```

In the code of your LLM app, log interactions with your agent using `phospho.log()`. 

```python
import phospho

# Your project id and api key are set as environment variables
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

Monitor and visualize your agent on the [phospho dashboard](https://platform.phospho.app/). 

## Usage

Read the docs at [docs.phospho.app](https://docs.phospho.app/) for more information. 
Use your phospho dashboard to monitor your agent, score interactions and detect events.