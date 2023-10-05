# phospho Python Client

This is a Python client for phospho.

For more information, see the docs at [docs.phospho.app](https://docs.phospho.app/).

Please note the project is still under development.

## Requirements

- Python 3.8 or higher

## Installation

```bash
pip install --upgrade phospho
```

## Getting started

Grab your API key from your phospho dashboard and set it as an environment variable:

```bash
export PHOSPHO_API_KEY="your-api-key"
```

Setup the project ID you want to work with (you can create a new project and get its ID from your dashboard):

```bash
export PHOSPHO_PROJECT_ID="your-project-id"
```

Create a new client instance:

```python
from phospho import Client

client = Client()
```

## Manage the sessions of your project

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

# Update the session content
# New keys will be added, existing keys will be updated
session.update(data={"your-key": "your value"})

# Make sure the ssession is up to date with the server
session.refresh()

# List all the tasks of the session
# Return a list of objects Task
tasks = session.list_tasks()

```

## Manage the tasks of your session

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

# Update the task content
# New keys will be added, existing keys will be updated
task.update(data={"your-key": "your value"})

# List all the steps of the task
# Return a list of objects Step
steps = task.list_steps()

```

## Manage the steps of your task

Create a new step:
```python
# Returns a new Step object
step = client.steps.create(task_id, input, name, status, is_last, additional_input=None, data=None)
"""
task_id: str
Id of the task the step belongs to

input: str
Input of the step (sometime called "the prompt")

name: str
Name of the step

status: str
Status of the step

is_last: bool
Whether the step is the last one of the task (usually, the output of the last step is the output of the task)

additional_input: dict=None
Additional input to be used with the step

data: dict=None
Additional data to be stored with the step
"""
```

Operations on a Step:
```python
# For a step already created
# Returns a Step object
step = client.steps.get("step-id-here")

# Get the step id
step.id

# Get the step content
step.content

# Refresh the step content
step.refresh()

# Update the step content
# New keys will be added, existing keys will be updated
step.update(status=None,is_last=None,output=None,additional_output=None, data=None)
"""
status: str=None
Status of the step

is_last: bool=None
Whether the step is the last one of the task (usually, the output of the last step is the output of the task)

output: str=None
Output of the step

additional_output: dict=None
Additional output of the step

data: dict=None
Additional data to be stored with the step
"""
```

## Usage

See the [documentation](https://docs.phospho.app/) for more information.