import os
import concurrent.futures
import logging
import inspect
import time
import pandas as pd


from phospho.client import Client
from phospho.tasks import Task
from phospho import extractor
from types import GeneratorType
from typing import List, Dict, Optional, Callable, Any, Literal
from collections import defaultdict

from random import sample

logger = logging.getLogger(__name__)
phospho_init = lambda **x: None
phospho_log = lambda **x: None


def adapt_task_to_agent_function(
    task: Task, agent_function: Callable[[Any], Any]
) -> Optional[Task]:
    """This function adapts a task to match the signature of an agent function.

    If the task is compatible with the agent function, this returns the task.

    If the task is not compatible with the agent function, this returns a new task that
    is compatible with the agent function, but that has less inputs.

    If nothing can be done, this returns None.
    """

    # The compatibility is based on the parameters names in the agent function signature
    agent_function_signature: inspect.Signature = inspect.signature(agent_function)
    task_inputs = set(task.content.additional_input.keys())
    agent_function_inputs = set(agent_function_signature.parameters.keys())

    if task_inputs == agent_function_inputs:
        # The task is compatible with the agent function
        return task
    elif task_inputs <= agent_function_inputs:
        # The agent function takes more inputs than the task provides
        # Check if those are optional in the agent function
        for key in agent_function_inputs - task_inputs:
            if (
                agent_function_signature.parameters[key].default
                is inspect.Parameter.empty
            ):
                # The agent function takes a non optional input that the task does not provide
                # We can't adapt the task to the agent function
                # Log what key is missing from the agent_function
                logger.warning(
                    f"Task {task.id} is not compatible with agent function {agent_function.__name__}: {key} is missing from the task"
                )
                return None
        # All of the additional inputs are optional in the agent function
        # So the task is compatible with the agent function
        return task
    elif task_inputs >= agent_function_inputs:
        # We filter the task to only keep the keys that are in the agent function signature
        new_task = Task(
            id=task.id,
            content={
                "input": {
                    key: task.content.input[key] for key in agent_function_inputs
                },
                "additional_input": task.content.additional_input,
                "output": task.content.output,
            },
        )
        # Log info that we filtered task inputs
        logger.info(
            f"Reduced the number of inputs of task {task.id} to match the agent function {agent_function.__name__}: removed {task_inputs - agent_function_inputs}"
        )
        return new_task
    else:
        # Check if the agent_function has an argument for any number of keyword arguments
        for param in agent_function_signature.parameters.values():
            if param.kind == inspect.Parameter.VAR_KEYWORD:
                # The agent function takes a **kwargs argument
                # The task is compatible with the agent function
                return task

    return None


class BacktestLoader:
    def __init__(
        self,
        client: Client,
        function_to_evaluate: Callable[[Any], Any],
        sample_size: Optional[int] = 10,
    ):
        self.sample_size = sample_size
        if self.sample_size < 0:
            raise ValueError("sample_size must be positive")

        # Pull the logs from phospho
        # TODO : Add time range filter
        # TODO : Add pull from dataset
        tasks = client.tasks.get_all()

        # TODO : Propper linkage of the task and the agent functions
        tasks_linked_to_function = [
            {"task": task, "agent_function": function_to_evaluate} for task in tasks
        ]

        # Filter the tasks to only keep the ones that are compatible with the agent function
        tasks_linked_to_function = []
        for task in tasks:
            adapted_task = adapt_task_to_agent_function(task, function_to_evaluate)
            if adapted_task is not None:
                tasks_linked_to_function.append(
                    {"task": adapted_task, "agent_function": function_to_evaluate}
                )

        # TODO : More complex sampling
        if self.sample_size is None:
            # None = all the tasks
            sampled_tasks = tasks_linked_to_function
        elif self.sample_size == 0:
            # 0 = no tasks
            sampled_tasks = []
        elif len(tasks_linked_to_function) > self.sample_size:
            # Downsample
            sampled_tasks = sample(tasks_linked_to_function, self.sample_size)
        elif len(tasks_linked_to_function) < self.sample_size:
            # Upsample
            # Duplicate the tasks
            duplicated_tasks = tasks_linked_to_function * int(
                1 + self.sample_size / len(tasks)
            )
            # Sample the remaining tasks
            sampled_tasks = tasks_linked_to_function + sample(
                duplicated_tasks,
                self.sample_size % len(duplicated_tasks)
                - len(tasks_linked_to_function),
            )
        else:
            sampled_tasks = tasks_linked_to_function

        self.sampled_tasks = sampled_tasks

    def __iter__(self):
        return iter(self.sampled_tasks)

    def __next__(self):
        return next(self.sampled_tasks)

    def __len__(self):
        return len(self.sampled_tasks)


class PandasLoader:
    def __init__(self, path: str, function_to_evaluate: Callable[[Any], Any]):
        if path.endswith(".csv"):
            self.dataset = pd.read_csv(path)
        elif path.endswith(".json"):
            self.dataset = pd.read_json(path)
        elif path.endswith(".xlsx"):
            self.dataset = pd.read_excel(path)
        else:
            raise NotImplementedError(
                f"File format {path.split('.')[-1]} is not supported. Supported formats: .csv, .json, .xlsx"
            )
        self.function_to_evaluate = function_to_evaluate

    def __iter__(self):
        return iter(self.dataset)

    def __next__(self):
        next_item = next(self.dataset)
        # TODO : Verify it has the right columns for the function_to_evaluate
        # Cast to Task
        task = Task(
            id=next_item["id"],
            content={
                "input": next_item["input"],
                "additional_input": next_item.get("additional_input", None),
                "output": next_item.get("output", None),
            },
        )
        return {
            "task": task,
            "agent_function": self.function_to_evaluate,
        }


class PhosphoTest:
    def __init__(
        self,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        executor_type: Literal["parallel", "sequential"] = "parallel",
    ):
        """
        This is used to backtest an agent with phospho.

        Sample code:

        ```
        phospho_test = phospho.PhosphoTest()

        @phospho_test.test
        def test_santa(**inputs):
            santa_claus_agent = SantaClausAgent()
            return santa_claus_agent.answer(**inputs)

        phospho_test.run()
        ```
        """
        # Execution parameter

        self.executor_type = executor_type
        self.client = Client(api_key=api_key, project_id=project_id)
        self.functions_to_evaluate: List[Callable[[Any], Any]] = []
        # Results are temporary stored in memory
        self.evaluation_results: Dict[str, int] = defaultdict(int)
        self.comparisons: List[dict] = []
        self.test_id: Optional[str] = None

    def test(self, fn: Callable[[Any], Any]) -> Callable[[Any], Any]:
        """
        Add this as a decorator on top of the evaluation function.
        """

        # TODO: Add task_name as a parameter
        # TODO: Add custom instructions for comparison and evaluation as a parameter

        self.functions_to_evaluate.append(fn)

        return fn

    def get_output_from_agent(
        self,
        additional_input: Any,
        agent_function: Callable[[Any], Any],
        execution_mode: str,
    ):
        """
        This function will return the output of the agent given an input
        """
        print(
            f"Calling {agent_function.__name__} with input {additional_input.__repr__()}"
        )

        # TODO : Make it so that that we use input or additional_input depending on the
        # signature (input type) of the agent function

        if execution_mode == "backtest":
            os.environ["PHOSPHO_EXECUTION_MODE"] = "backtest"
        new_output = agent_function(**additional_input)

        # Handle generators
        if isinstance(new_output, GeneratorType):
            full_resp = ""
            for response in new_output:
                full_resp += response or ""
                new_output_str = extractor.detect_str_from_output(full_resp)
            else:
                new_output_str = extractor.detect_str_from_output(new_output)
        return new_output_str

    def evaluate(self, task_to_evaluate: Dict[str, Any]):
        """
        Run the evaluation pipeline on the task
        """

        task = task_to_evaluate["task"]
        agent_function = task_to_evaluate["agent_function"]

        # Get the output from the agent
        context_input = task.content.input
        new_output_str = self.get_output_from_agent(
            additional_input=task.content.additional_input,
            agent_function=agent_function,
            execution_mode="evaluate",
        )

        # Ask phospho: what's the best answer to the context_input ?
        print(f"Evaluating with phospho (task: {task.id})")
        phospho_log(
            input=context_input,
            output=new_output_str,
            test_id=self.test_id,
        )

    def compare(
        self, task_to_compare: Dict[str, Any]
    ) -> None:  # task: Task, agent_function: Callable[[Any], Any]):
        """
        Compares the output of the task with the output of the agent function
        """

        task = task_to_compare["task"]
        agent_function = task_to_compare["agent_function"]
        print("Comparing task id: ", task.id)

        # Get the output from the agent
        context_input = task.content.input
        old_output_str = task.content.output
        new_output_str = self.get_output_from_agent(
            additional_input=task.content.additional_input,
            agent_function=agent_function,
            execution_mode="compare",
        )

        # Ask phospho: what's the best answer to the context_input ?
        print(f"Comparing with phospho (task: {task.id})")
        self.client.compare(
            context_input,
            old_output_str,
            new_output_str,
        )

    def run(
        self,
        source_loader: Literal["backtest", "pandas"] = "backtest",
        source_loader_params: Optional[Dict[str, Any]] = None,
        metrics: Optional[List[Literal["compare", "evaluate"]]] = None,
    ):
        """
        Backtesting: This function pull all the tasks logged to phospho and run the agent on them.
        """

        if source_loader_params is None:
            source_loader_params = {}
        if metrics is None:
            # Default metric is compare
            metrics = ["compare"]

        if len(self.functions_to_evaluate) == 0:
            raise ValueError(
                "You need to add at least one function to evaluate with the @phospho_test.test decorator"
            )
        elif len(self.functions_to_evaluate) > 1:
            raise NotImplementedError(
                "Only one function to evaluate is supported for now"
            )

        # Start timer
        start_time = time.time()

        # TODO : Get the test_id
        self.test_id = self.client.create_test()

        if source_loader == "backtest":
            tasks_linked_to_function = BacktestLoader(
                client=self.client,
                function_to_evaluate=self.functions_to_evaluate[0],
                **source_loader_params,
            )
        elif source_loader == "pandas":
            tasks_linked_to_function = PandasLoader(
                function_to_evaluate=self.functions_to_evaluate[0],
                **source_loader_params,
            )
        else:
            raise NotImplementedError(
                f"Source loader {source_loader} is not implemented"
            )

        for metric in metrics:
            if metric == "evaluate":
                from phospho import init as phospho_init
                from phospho import log as phospho_log

                # For evaluate, we'll need to init phospho and use .log
                phospho_init(self.client.api_key, self.client.project_id)
                evaluation_function = self.evaluate
            elif metric == "compare":
                evaluation_function = self.compare
            else:
                raise NotImplementedError(
                    f"Metric {metric} is not implemented. Implemented metrics: 'compare', 'evaluate'"
                )

            # Evaluate the tasks in parallel
            if self.executor_type == "parallel":
                with concurrent.futures.ThreadPoolExecutor() as executor:
                    # Submit tasks to the executor
                    # executor.map(self.evaluate_a_task, task_to_evaluate)
                    executor.map(evaluation_function, tasks_linked_to_function)
            elif self.executor_type == "sequential":
                for task_function in tasks_linked_to_function:
                    evaluation_function(
                        task_function["task"], task_function["agent_function"]
                    )
            else:
                raise NotImplementedError(
                    f"Executor type {self.executor_type} is not implemented"
                )

        # Stop timer
        end_time = time.time()

        # Display a summary of the results
        print("Phospho backtest results:")
        print(f"Total number of tasks: {len(tasks_linked_to_function)}")
        print(f"Total time: {end_time - start_time} seconds")

        # TODO : Fetch the results from the backend
        # TODO : Display the results
