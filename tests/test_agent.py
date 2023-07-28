import pytest
from phospho import Agent 

@pytest.fixture
def agent_instance():
    return Agent(name="TestAgent", cpu=2, memory="8Gi", python_version="python3.9")

def test_agent_attributes(agent_instance):
    assert agent_instance.name == "TestAgent"
    assert agent_instance.cpu == 2
    assert agent_instance.memory == "8Gi"
    assert agent_instance.python_version == "python3.9"
    assert agent_instance.python_packages == ""

def test_agent_custom_routes(agent_instance):
    @agent_instance.ask()
    def custom_ask_route(*args, **kwargs):
        return "Custom ask route response"

    assert agent_instance.handle_ask_request("default") == "Custom ask route response"

def test_unknown_ask_route(agent_instance):
    with pytest.raises(ValueError):
        agent_instance.handle_ask_request("unknown_route_id")

def test_agent_with_python_packages():
    python_packages_list = ["numpy", "pandas", "matplotlib"]
    agent_instance_with_packages = Agent(name="AgentWithPackages", python_packages=python_packages_list)

    assert agent_instance_with_packages.name == "AgentWithPackages"
    assert agent_instance_with_packages.python_packages == python_packages_list

def test_define_and_ask_hello(agent_instance):
    @agent_instance.ask()
    def question(message):
        response = f"Hello {message}"
        return response
    assert agent_instance.handle_ask_request("default", "World") == "Hello World"

