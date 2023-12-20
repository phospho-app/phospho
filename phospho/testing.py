import os
import concurrent.futures
import logging
import inspect

from phospho.client import Client
from phospho.tasks import Task
from phospho import extractor
from types import GeneratorType
from typing import List, Dict, Optional, Callable, Any, Literal
from collections import defaultdict

from random import sample
from pprint import pprint

logger = logging.getLogger(__name__)


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


class PhosphoTest:
    def __init__(
        self,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        executor_type: Literal["parallel", "sequential"] = "parallel",
        sample_size: Optional[int] = 2,
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
        self.sample_size = sample_size
        if self.sample_size < 0:
            raise ValueError("sample_size must be positive")
        self.executor_type = executor_type

        self.client = Client(api_key=api_key, project_id=project_id)
        self.functions_to_evaluate: List[Callable[[Any], Any]] = []
        # Results are temporary stored in memory
        self.evaluation_results: Dict[str, int] = defaultdict(int)
        self.comparisons: List[dict] = []

    def test(self, fn):
        """This is a de corator to add on top of functions
        to test them with the phospho backend
        """

        self.functions_to_evaluate.append(fn)

        return fn

    def get_output_from_agent(
        self, additional_input: Any, agent_function: Callable[[Any], Any]
    ):
        """
        This function will return the output of the agent given an input
        """
        print(
            f"Calling {agent_function.__name__} with input {additional_input.__repr__()}"
        )

        # TODO : Handle the case 'there are more keys in additional_inputs than in the agent_function signature'
        # TODO : Handle the case 'there are more keys in the agent_function signature than in additional_inputs'

        # check the value of PHOSPHO_EXECUTION_MODE
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

    def evaluate_a_task(
        self, task_to_evaluate: Dict[str, Any]
    ):  # task: Task, agent_function: Callable[[Any], Any]):
        """This function evaluates a single task using the phospho backend"""

        task = task_to_evaluate["task"]
        agent_function = task_to_evaluate["agent_function"]

        print("Task id: ", task.id)

        # try:
        # if True:
        # Get the output from the agent
        context_input = task.content.input
        old_output_str = task.content.output
        new_output_str = self.get_output_from_agent(
            task.content.additional_input, agent_function
        )

        # Ask phospho: what's the best answer to the context_input ?
        print(f"Comparing with phospho (task: {task.id})")
        comparison_result = self.client.compare(
            context_input,
            old_output_str,
            new_output_str,
        )

        # Collect the results
        print(f"Collecting results (task: {task.id})")
        self.comparisons.append(
            {
                "input": task.content.input,
                "old": task.content.output,
                "new": new_output_str,
            }
        )
        self.evaluation_results[comparison_result.comparison_result] += 1

        # except Exception as e:
        #     logger.error(f"Error while answering task {task.id}: {e}")

    def run(self):
        """
        Backtesting: This function pull all the tasks logged to phospho and run the agent on them.
        """

        # Pull the logs from phospho
        # TODO : Add time range filter
        # TODO : Add pull from dataset
        tasks = self.client.tasks.get_all()

        # TODO : Propper linkage of the task and the agent functions
        tasks_linked_to_function = [
            {"task": task, "agent_function": self.functions_to_evaluate[0]}
            for task in tasks
        ]

        # Filter the tasks to only keep the ones that are compatible with the agent function
        tasks_linked_to_function = [
            {
                "task": adapt_task_to_agent_function(
                    task["task"], task["agent_function"]
                ),
                "agent_function": task["agent_function"],
            }
            for task in tasks_linked_to_function
            if adapt_task_to_agent_function(task["task"], task["agent_function"])
            is not None
        ]

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

        # Evaluate the tasks in parallel
        if self.executor_type == "parallel":
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Submit tasks to the executor
                # executor.map(self.evaluate_a_task, task_to_evaluate)
                executor.map(self.evaluate_a_task, sampled_tasks)
        elif self.executor_type == "sequential":
            for task in sampled_tasks:
                self.evaluate_a_task(task)
        else:
            raise NotImplementedError(
                f"Executor type {self.executor_type} is not implemented"
            )

        # Display a summary of the results
        print("Phospho backtest results:")
        # pprint(self.comparisons)
        pprint(self.evaluation_results)

        # TODO : Push the results to phospho
