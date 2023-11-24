import pytest
import json

from phospho import Client

from phospho.tasks import Task
from phospho.steps import Step

@pytest.fixture
def client_instance():
    # env variables define the api key and project id
    return Client()

def test_client_sessions(client_instance):
    # Create a session
    session = client_instance.sessions.create(data={"name": "test session"})

    detect = False
    for session_obj in client_instance.sessions.list():
        if session_obj.id == session.id:
            detect = True
            break

    assert detect, "Session not found"

    # Get a session
    session_bis = client_instance.sessions.get(session.id)
    assert session_bis.content == session.content, "Session content not equal"

    # Update a session
    new_content = {"name": "test session 2", "test": "test"}
    session.update(data=new_content)

    session.refresh()

    assert session.content["data"] == new_content, "Session content not equal"

    # Update a session
    new_content = {"name": "test session 2", "test": "test"}
    session.update(metadata={"flag": "success"})

    session.refresh()
    # Check the metadata contains the flag
    assert session.content["metadata"]["flag"] == "success", "Session metadata not equal"

    # Update a session
    session.update(metadata={"flag": "success"}, data=new_content)
    # Check the data and the metadata contains the flag
    assert session.content["metadata"]["flag"] == "success", "Session metadata not equal"
    assert session.content["data"] == new_content, "Session content not equal"

    # Update 

    session.refresh()

    assert session.content["data"] == new_content, "Session content not equal"

    # Tasks

    tasks = session.list_tasks()

    assert len(tasks) == 0, "Session should not have any tasks"

    # Create a Task
    task = client_instance.tasks.create(session_id=session.id, sender_id="sender_id", input="input")

    # Check if task is created successfully
    assert isinstance(task, Task)

    # Get the task
    retrieved_task = client_instance.tasks.get(task.id)

    # Refresh the task
    task.refresh()

    # Check if the retrieved task's content matches the created task's content
    assert json.dumps(retrieved_task.content, sort_keys=True) == json.dumps(task.content, sort_keys=True)

    # Update the task
    updated_task = task.update(data={"new_data": "updated_data"})

    # Check if the updated task's content matches the expected content
    assert updated_task.content["data"]["new_data"] == "updated_data"

    # List steps for the task
    steps = task.list_steps()

    # Check if steps is a list of Step objects
    assert all(isinstance(step, Step) for step in steps)

    # Create a Task using the TaskCollection
    task = client_instance.tasks.create(session_id=session.id, sender_id="sender_id", input="input")

    # Check if task is created successfully
    assert isinstance(task, Task)

    # Get the task using the TaskCollection
    retrieved_task = client_instance.tasks.get(task.id)

    # Check if the retrieved task's content matches the created task's content
    assert json.dumps(retrieved_task.content, sort_keys=True) == json.dumps(task.content, sort_keys=True)

    ### STEPS ###

    # Create a Step
    step = client_instance.steps.create(task_id=task.id, input="input", name="name", status="status", is_last=True)

    # Check if step is created successfully
    assert isinstance(step, Step)

    # Refresh the step
    step.refresh()

    # Get the step
    retrieved_step = client_instance.steps.get(step.id)

    print("retrieved step content :", retrieved_step.content)

    # Check if the retrieved step's content matches the created step's content
    assert json.dumps(retrieved_step.content, sort_keys=True) == json.dumps(step.content, sort_keys=True)

    # Update the step
    updated_step = step.update(data={"key": "value"})

    print(updated_step.content)


