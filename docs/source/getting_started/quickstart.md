---
title: Getting Started
sidebar_position: 2
---

# Getting Started

[phospho](https://phospho-portal-git-alpha-phospho-team.vercel.app/) is a platform to monitor what your users are talking about on your LLM-app. It collects logs from your LLM app, analyze them, and display the result on the phospho dashboards. 

> :warning: The project is in **Alpha**. Expect frequent changes and updates!

## 1. Install the python sdk

```bash
pip install --upgrade phospho
```

## 2. Setup your phospho environment

Go to the [phospho platform](https://phospho-portal-git-alpha-phospho-team.vercel.app/) and sign up.

### 2.a Get a phospho project id

Create your first project. You might need to wait a few seconds and refresh the page to see your project.

Select project in the dropdown menu on the top left of the page. 

Then, go to settings and copy the project id.

In your code, add the following environment variable :

```bash
export PHOSPHO_PROJECT_ID="your_project_id"
```

### 2.b Get your phospho API key

Go to *Settings*, then *Manage phospho API Keys* and create a new API key.

In your code, add the following environment variable :

```bash
export PHOSPHO_API_KEY="your_api_key"
```

## 3. Start recording interactions on your LLM app

### Passing explicit inputs and outputs

phospho lets you explicitely register interactions between the user and your LLM app. An interaction is made of two things:
- `input (str)`: this is what your user asks to your app. 
- `output (str)`: this is what the app replies to the user.

```python
import phospho

# By default, phospho reads the PHOSPHO_PROJECT_ID and PHOSPHO_API_KEY from the environment variables
phospho.init()

# Example
input = "Hello! This is what the user asked to the system :)"
output = "This is the response showed to the user by the app."

# This is how you log an interactions to phospho
phospho.log(input=input, output=output)
```

### Passing directly OpenAI inputs and responses

phospho aims to be battery included. So if you pass something else than a `str` to `phospho.log`, phospho will try to extract what's usually considered "the input" or "the output". 

For example, if you are using the OpenAI API, you can just do:

```python
import openai
import phospho

phospho.init(api_key="phospho-key", project_id="phospho-project-id")
openai_client = openai.OpenAI(api_key="openai-key")

input_prompt = "Explain quantum computers in less than 20 words."

# This is your LLM app code
query = {
    "messages": [{"role": "system", "content": "You are a helpful assistant."},
                 {"role": "user", "content": input_prompt},
    ], 
    "model": "gpt-3.5-turbo", 
}
response = openai_client.chat.completions.create(**query)

# You can directly pass as dict or a ChatCompletion as input and output
log = phospho.log(input=query, output=response)
print("input:", log["input"])
print("output:", log["output"])
```

Result:
```text
input: Explain quantum computers in less than 20 words.
output: Qubits harness quantum physics for faster, more powerful computation.
```

### Logging additional metadata

You can log whatever you want. 

```python
log = phospho.log(
    input="log this", output="and that", 
    raw_input={"more": "details"},
    raw_output={"even": "more"},
    metadata={"always": "moooore"},
    log_anything_and_everything="even_this",
)
```

# Using the webapp

phospho store and analyze your logs, then display them in a [webapp](https://phospho-portal-git-alpha-phospho-team.vercel.app/).

## Monitoring custom events

phospho enables you to detect custom events in your app. Here are examples of events:
- The user is trying to book a flight 
- The assistant responded something that could be considered financial advice
- The assistant started with 'As an AI language model'
- The user uses slang that the LLM didn't understand
- The user thanked the agent for its help

Events help you define and discover user behaviour on your conversational app. 

You are the one that define what events you want to look for.

To define an event, go to the *Settings* tab of your [dashboard](https://phospho-portal-git-alpha-phospho-team.vercel.app/). You can define the event name and the event description.

For exemple :
- Event name : stop_request
- Description : The user asks the assistant to stop sending messages.

As a best practice, you should refere to your user as "the user" and to your LLM app as "the assistant".

Every time you log an interaction, phospho will try to detect if an event occured. If an event occured, it will be logged to phospho.

## Visualizing the results

phospho comes with data visualization that gives you quick insights about your LLM apps.

Go to the *Dashboard* tab of your [dashboard](https://phospho-portal-git-alpha-phospho-team.vercel.app/). 

- On the *Dashboard* tab, you can see the number of sessions logged to phospho and the number of events that were detected.
- On the *Sessions* tab, you can deep-dive in every session. If events were detected, you can see them in the *Events* column. You can click on a session to view its transcript.
- On the *Settings* tab, you can define the events that you want to monitor.