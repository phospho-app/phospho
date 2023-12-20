import os
import concurrent.futures
import logging

from phospho.client import Client
from phospho.tasks import Task
from phospho import extractor
from types import GeneratorType
from typing import List, Dict, Optional, Callable, Any
from collections import defaultdict

from random import sample
from pprint import pprint

logger = logging.getLogger(__name__)


class PhosphoTest:
    def __init__(
        self,
        api_key: Optional[str] = None,
        project_id: Optional[str] = None,
    ):
        self.evaluation_results: Dict[str, int] = defaultdict(int)
        self.comparisons: List[dict] = []
        self.client = Client(api_key=api_key, project_id=project_id)
        self.functions_to_evaluate: List[Callable[[Any], Any]] = []

        # Initialize phospho in backtest mode
        os.environ["PHOSPHO_EXECUTION_MODE"] = "backtest"

    def test(self, fn):
        """This is a de corator to add on top of functions
        to test them with the phospho backend
        """

        self.functions_to_evaluate.append(fn)

        return fn

    def get_output_from_agent(self, input: Any, agent_function: Callable[[Any], Any]):
        """
        This function will return the output of the agent given an input
        """
        new_output = agent_function(**input)
        # Handle generators
        if isinstance(new_output, GeneratorType):
            full_resp = ""
            for response in new_output:
                full_resp += response or ""
                new_output_str = extractor.detect_str_from_output(full_resp)
            else:
                new_output_str = extractor.detect_str_from_output(new_output)
        return new_output_str

    def evaluate_a_task(self, task: Task, agent_function: Callable[[Any], Any]):
        """This function evaluates a single task using the phospho backend"""

        try:
            print("Task id: ", task.id)
            context_input = task.content["input"]
            old_output_str = task.content["output"]
            new_output_str = self.get_output_from_agent(
                task.content["additional_input"]
            )

            # Ask phospho: what's the best answer to the context_input ?
            comparison_result = self.client.compare(
                context_input,
                old_output_str,
                new_output_str,
            )

            # Collect the results
            self.comparisons.append(
                {
                    "input": task.content["input"],
                    "old": task.content["output"],
                    "new": new_output_str,
                }
            )
            self.evaluation_results[comparison_result.comparison_result] += 1

        except Exception as e:
            logger.error(f"Error while answering task {task.id}: {e}")

    def run(self):
        """
        Backtesting: This function pull all the tasks logged to phospho and run the agent on them.

        TODO: This should be abstracted. The user should be able to run this with a single command
        and basic filters, such as the agent to test, the project fetch tasks from, the time range, etc.
        """

        # Pull the logs from phospho
        tasks = self.client.tasks.get_all()
        if len(tasks) > 10:
            tasks = sample(tasks, 10)

        # TODO : Propper linkage of the task and the agent functions
        task_to_evaluate = {
            "task": tasks,
            "agent_function": self.functions_to_evaluate[0],
        }

        # Evaluate the tasks in parallel
        with concurrent.futures.ThreadPoolExecutor() as executor:
            # Submit tasks to the executor
            executor.map(self.evaluate_a_task, task_to_evaluate)

        # Display a summary of the results
        pprint(self.comparisons)
        print(self.evaluation_results)

        # TODO : Push the results to phospho
