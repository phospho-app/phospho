import pytest
from phospho import Agent, Message

@pytest.fixture
def agent_instance():
    return Agent(name="TestAgent")

def test_agent_attributes(agent_instance):
    assert agent_instance.name == "TestAgent"

def test_agent_custom_routes(agent_instance):
    @agent_instance.ask()
    def custom_ask_route(*args, **kwargs):
        return "Custom ask route response"

    assert agent_instance.handle_ask_request() == "Custom ask route response"

def test_unknown_ask_route(agent_instance):
    with pytest.raises(ValueError):
        agent_instance.handle_ask_request("unknown_route_id")

def test_agent_with_version_number():
    version_number = "0.0.1"
    agent_instance_with_packages = Agent(name="AgentWithPackages", version=version_number)

    assert agent_instance_with_packages.name == "AgentWithPackages"
    assert agent_instance_with_packages.version == version_number

def test_define_and_ask_hello(agent_instance):
    # Define message
    message = Message(content="World!", payload={}, metadata={})

    @agent_instance.ask()
    def question(message):
        response = f"Hello {message.content}"
        return response
    assert agent_instance.handle_ask_request(message) == "Hello World!"

def test_custom_args(agent_instance):
    # Define message
    message = Message(content="World!", payload={}, metadata={})

    arg1 = 1
    arg2 = 2

    @agent_instance.ask()
    def question(message):
        response = f"Hello {message.content}, the sum of {arg1} and {arg2} is {arg1+arg2}"
        return response
    assert agent_instance.handle_ask_request(message) == "Hello World!, the sum of 1 and 2 is 3"

def test_ask_with_options(agent_instance):
    # Define message
    message = Message(content="World!", payload={}, metadata={})

    @agent_instance.ask(stream=True)
    def question(message):
        response = f"Hello {message.content}"
        return response
    assert agent_instance.handle_ask_request(message) == "Hello World!"

def test_agent_empty_context(agent_instance):
    # Define message
    message = Message(content="World!", payload={}, metadata={})

    assert agent_instance.context['session_id'].get() == None


def test_agent_context(agent_instance):
    # Define message
    message = Message(content="World!", payload={}, metadata={})

    new_session_id = "12345"
    agent_instance.update_session_id(new_session_id)

    @agent_instance.ask()
    def question(message):
        response = f"Hello {message.content}, your session id is {agent_instance.context['session_id'].get()}"
        return response
    assert agent_instance.handle_ask_request(message) == f"Hello World!, your session id is {new_session_id}"

def test_agent_session_set_id(agent_instance):
    # Define message
    message = Message(content="World!", payload={}, metadata={})

    new_session_id = "12345"
    agent_instance.update_session_id(new_session_id)

    assert agent_instance.session.return_session_id() == new_session_id
    