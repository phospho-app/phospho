import imp
import os
import os.path
from typing import Optional

import typer
from rich import print
from typing_extensions import Annotated
from enum import Enum
from ._version import __version__

app = typer.Typer()


class ExecutorType(Enum):
    SEQUENTIAL = "sequential"
    PARALLEL = "parallel"


def load_from_file(filepath):
    mod_name, file_ext = os.path.splitext(os.path.split(filepath)[-1])

    if file_ext.lower() == ".py":
        py_mod = imp.load_source(mod_name, filepath)
    elif file_ext.lower() == ".pyc":
        py_mod = imp.load_compiled(mod_name, filepath)
    else:
        raise ImportError(f"Unknown file type {file_ext}")

    return py_mod


def version_callback(value: bool):
    """
    Print the current version of phospho
    """
    if value:
        print(f"[green]v{__version__}[/green]")
        raise typer.Exit()


@app.callback(invoke_without_command=True)
def callback(
    version: Annotated[
        Optional[bool],
        typer.Option("--version", callback=version_callback, help="Print the version"),
    ] = None,
):
    """
    phospho: a command line interface for the phospho platform

    Learn more: https://docs.phospho.ai
    """
    print("[green][bold]Welcome to 🧪phospho[/bold][/green] ")
    print("-> API keys & Project ids: https://platform.phospho.ai")
    print("-> Run 'phospho init' to configure a new project")
    print("-> Run 'phospho test' to run tests")
    print("-> Run 'phospho --help' for more")
    print("")


@app.command()
def init(
    phospho_api_key: Annotated[
        str,
        typer.Option(
            envvar="PHOSPHO_API_KEY",
            help="The phospho API key, owner of the project",
            prompt=True,
            hide_input=True,
        ),
    ],
    phospho_project_id: Annotated[
        str,
        typer.Option(
            envvar="PHOSPHO_PROJECT_ID",
            help="The project id of the phospho project",
            prompt=True,
        ),
    ],
    global_config: Annotated[
        str,
        typer.Option(
            help="The path to the global config file, where the API key and project id are stored.",
        ),
    ] = "~/.phospho/config",
    test_file: Annotated[
        str,
        typer.Option(
            help="The path to the test file that will be created.",
        ),
    ] = "phospho_test.py",
):
    """
    Initialize the phospho project
    """

    # Create the global config file
    global_config = os.path.expanduser(global_config)
    os.makedirs(os.path.dirname(global_config), exist_ok=True)
    with open(global_config, "w") as f:
        f.write(f"PHOSPHO_API_KEY={phospho_api_key}\n")
        f.write(f"PHOSPHO_PROJECT_ID={phospho_project_id}\n")

    # Try to read it back
    with open(global_config, "r") as f:
        print(f"Configuration saved in: {global_config}")

    # Create the default test file
    # if it exists, do not overwrite it
    full_test_file = os.path.abspath(test_file)
    if os.path.exists(full_test_file):
        print(
            f"File {full_test_file} already exists. If you want to create a new one, delete this one first."
        )
    else:
        with open(test_file, "w") as f:
            f.write(
                """
def main():
    print("Running tests")
                """
            )
        print(f"Default test file created: {full_test_file}")
    print("")
    print("[green][bold]🧪phospho tests initialized![bold][/green]")
    print(f"-> Edit the test file '{test_file}' to add your tests")
    print("-> Run 'phospho test' to run tests")


@app.command()
def test(
    executor_type: Annotated[
        ExecutorType, typer.Option(help="The type of executor to use.")
    ] = "parallel",
    max_parallelism: Annotated[
        int,
        typer.Option(
            help="If executor_type is parallel, the maximum number of parallel tests to trigger.",
        ),
    ] = 20,
    test_file: Annotated[
        str,
        typer.Option(
            help="The python file that runs tests. The function main() should be defined in this file.",
        ),
    ] = "phospho_testing.py",
    phospho_api_key: Annotated[
        Optional[str],
        typer.Option(
            envvar="PHOSPHO_PROJECT_ID",
            help="The phospho API key owner of the project",
        ),
    ] = None,
    phospho_project_id: Annotated[
        Optional[str],
        typer.Option(
            envvar="PHOSPHO_PROJECT_ID",
            help="The project id of the phospho project",
        ),
    ] = None,
    global_config: Annotated[
        str,
        typer.Option(
            help="The path to the global config file, where the API key and project id are stored.",
        ),
    ] = "~/.phospho/config",
):
    """
    Run tests for the project on the specified file.

    The file should contain a function called main() that runs the tests.
    """

    if phospho_api_key is None or phospho_project_id is None:
        # Load the global config
        global_config = os.path.expanduser(global_config)
        if not os.path.exists(global_config):
            print(
                f"Global config not found at {global_config}\nRun 'phospho init' to create one"
            )
            raise typer.Exit()
        with open(global_config, "r") as f:
            # Replace missing values with the ones from the global config
            for line in f:
                key, value = line.strip().split("=")
                if key == "PHOSPHO_API_KEY" and phospho_api_key is None:
                    phospho_api_key = value
                elif key == "PHOSPHO_PROJECT_ID" and phospho_project_id is None:
                    phospho_project_id = value

    if phospho_api_key is not None and phospho_project_id is not None:
        os.environ["PHOSPHO_API_KEY"] = phospho_api_key
        os.environ["PHOSPHO_PROJECT_ID"] = phospho_project_id
        print("Config loaded")
    else:
        print(
            "No phospho API key or project id found. Run 'phospho init' to create one."
        )
        raise typer.Exit()

    # Verify if the test file exists
    full_test_file = os.path.abspath(test_file)
    if not os.path.exists(test_file):
        print(
            f"File {full_test_file} not found.\nRun 'phospho init' to create a default one."
        )
        raise typer.Exit()

    try:
        print(f"Running tests: {test_file}")
        module = load_from_file(full_test_file)
        # This assumes there is an object called phospho_test
        module.phospho_test.run(
            executor_type=executor_type.value, max_parallelism=max_parallelism
        )
        module.phospho_test.flush()
    except ModuleNotFoundError as e:
        print(f"Module {test_file} not found {e}.\nRun 'phospho init' to create one.")
    except ImportError as e:
        print(
            f"Error importing {test_file} module: {e}.\nRun 'phospho init' to create one."
        )
    except AttributeError as e:
        print(
            f"Error running tests in {test_file}: {e}.\nMake sure the function main() is defined."
        )
