import os
import concurrent.futures
import logging

from phospho.client import Client
from phospho.tasks import Task
from phospho import extractor
from types import GeneratorType
from typing import List, Dict, Optional, Callable, Any, Literal
from collections import defaultdict

from random import sample
from pprint import pprint

logger = logging.getLogger(__name__)


class PhosphoTest:
    def __init__(
        self,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
        executor_type: Literal["parallel", "sequential"] = "parallel",
        sample_size: Optional[int] = 10,
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
        self.executor_type = executor_type

        self.client = Client(api_key=api_key, project_id=project_id)
        self.functions_to_evaluate: List[Callable[[Any], Any]] = []
        # Results are temporary stored in memory
        self.evaluation_results: Dict[str, int] = defaultdict(int)
        self.comparisons: List[dict] = []

        # Initialize phospho in backtest mode
        os.environ["PHOSPHO_EXECUTION_MODE"] = "backtest"

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
        tasks = self.client.tasks.get_all()
        # TODO : Add a 'sample_size' with upsampling if the number of tasks is too small
        if len(tasks) > self.sample_size:
            # Downsample
            sampled_tasks = sample(tasks, self.sample_size)
        elif len(tasks) < self.sample_size:
            # Upsample
            # Duplicate the tasks
            duplicated_tasks = tasks * int(1 + self.sample_size / len(tasks))
            # Sample the remaining tasks
            sampled_tasks = tasks + sample(
                duplicated_tasks, self.sample_size % len(duplicated_tasks)
            )
        elif self.sample_size == None:
            sampled_tasks = tasks
        else:
            sampled_tasks = tasks

        # if len(tasks) > 10:
        #     tasks = sample(tasks, 10)

        # TODO : Propper linkage of the task and the agent functions
        task_to_evaluate = [
            {"task": task, "agent_function": self.functions_to_evaluate[0]}
            for task in sampled_tasks
        ]

        # Evaluate the tasks in parallel
        if self.executor_type == "parallel":
            with concurrent.futures.ThreadPoolExecutor() as executor:
                # Submit tasks to the executor
                # executor.map(self.evaluate_a_task, task_to_evaluate)
                executor.map(self.evaluate_a_task, task_to_evaluate)
        elif self.executor_type == "sequential":
            for task in task_to_evaluate:
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
