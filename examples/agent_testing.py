"""
This is an example of how to backtest an agent with phospho
"""
import phospho
import logging
import os
import concurrent.futures

from collections import defaultdict
from pprint import pprint
from types import GeneratorType
from typing import Any, Dict, List
from random import sample


# This is the agent to test
from streamlit_santa_agent.backend import SantaClausAgent

logger = logging.getLogger(__name__)


def get_output_from_agent(input: Dict[str, Any]) -> str:
    """
    This function will return the output of the agent given an input

    TODO: The detection of the functions to call, and how to call them
    (ex: instatiate object, stream outputs, use async, casting inputs, etc.)
    should be done automatically by the phospho module.
    """
    santa_claus_agent = SantaClausAgent()
    new_output = santa_claus_agent.answer(**input)

    # If generator, we need to extract the str from the output
    if isinstance(new_output, GeneratorType):
        full_resp = ""
        for response in new_output:
            full_resp += response or ""
        new_output_str = phospho.extractor.detect_str_from_output(full_resp)
    else:
        new_output_str = phospho.extractor.detect_str_from_output(new_output)

    return new_output_str


def evaluate_a_task(task):
    """This function evaluates a single task using the phospho backend"""
    global EVALUATION_RESULTS
    global COMPARISONS

    try:
        print("Task id: ", task.id)
        new_output_str = get_output_from_agent(task.content["additional_input"])

        #
        comparison_result = phospho.client.compare(
            task.content["input"],
            task.content["output"],
            new_output_str,
        )

        # Collect the results
        COMPARISONS.append(
            {
                "input": task.content["input"],
                "old": task.content["output"],
                "new": new_output_str,
            }
        )
        EVALUATION_RESULTS[comparison_result.comparison_result] += 1

    except Exception as e:
        logger.error(f"Error while answering task {task.id}: {e}")


# We'll collect evaluation in dict
EVALUATION_RESULTS: Dict[str, int] = defaultdict(int)
COMPARISONS: List[dict] = []


def main():
    """
    Backtesting: This function pull all the tasks logged to phospho and run the agent on them.

    TODO: This should be abstracted. The user should be able to run this with a single command
    and basic filters, such as the agent to test, the project fetch tasks from, the time range, etc.
    """
    # Initialize phospho in backtest mode
    os.environ["PHOSPHO_EXECUTION_MODE"] = "backtest"
    phospho.init(project_id="jRg9zVIXRTqmokv84wSt")

    # Pull the logs from phospho
    tasks = phospho.client.tasks.get_all()
    if len(tasks) > 10:
        tasks = sample(tasks, 10)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit tasks to the executor
        executor.map(evaluate_a_task, tasks)

    # Display a summary of the results
    pprint(COMPARISONS)
    print(EVALUATION_RESULTS)


if __name__ == "__main__":
    main()
