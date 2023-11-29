# phospho Python Client

Phospho is a platform to help you monitor LLM apps.

Read the docs at [docs.phospho.app](https://docs.phospho.app/).

> This project is still under active development!

## Installation of the phospho client

You need Python `>=3.8`

```bash
pip install --upgrade phospho
```

## Quickstart

Create a phospho account and go to the [phospho dashboard](phospho.app). Create an API key and create a project. Set them as environment variables:


```bash
export PHOSPHO_PROJECT_ID="project-id"
export PHOSPHO_API_KEY="your-api-key"
```

In your LLM app, log interactions with your agent using `phospho.log()`. Monitor and visualize your agent on the [phospho dashboard](phospho.app). 

```python
import phospho
import openai

phospho.init()
openai_client = openai.OpenAI()

# This is your agent code
query = {
    "messages": [{"role": "user", "content": "Say this is a test"}], 
    "model": "gpt-3.5-turbo", 
}
response = openai_client.chat.completions.create(**query)

# This is how you log it to phospho
phospho.log(input=query, output=response)
```

Read the docs at [docs.phospho.app](https://docs.phospho.app/) to go further. 

## Access the sessions of your project

Create a new session:
```python
# Returns a new Session object
session = client.sessions.create(data=None)
"""
data: dict=None
Additional data to be stored with the session
"""
```

List all the sessions of your project:
```python
# Returns a list of objects Session
sessions = client.sessions.list()
```

Operations on a session:
```python
# For a session already created
# Returns a new Session object
session = client.sessions.get("session-id-here")

# Get the session id
session.id

# Get the session content
session.content

# List all the tasks of the session
# Return a list of objects Task
tasks = session.list_tasks()

```

## Access the tasks of your session

Create a new task:
```python
# Returns a new Task object
task = client.tasks.create(session_id, sender_id, input, additional_input=None, data=None)
"""
session_id: str
Id of the session the task belongs to

sender_id: str
Identifier of the sender of the task, can be null

input: str
Input of the task (sometime called "the prompt")

additional_input: dict=None
Additional input to be used with the task

data: dict=None
Additional data to be stored with the task
"""
```

Operations on a Task:
```python
# For a task already created
# Returns a Task object
task = client.tasks.get("task-id-here")

# Get the task id
task.id

# Get the task content
task.content

# Refresh the task content
task.refresh()
```


## Usage

See the [documentation](https://docs.phospho.app/) for more information.