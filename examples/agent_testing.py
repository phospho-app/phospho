"""
This is an example of how to backtest an agent with phospho
"""
import phospho
import logging
import os
import concurrent.futures

from openai import OpenAI
from collections import defaultdict
from pprint import pprint
from types import GeneratorType
from typing import Any, Dict
from random import sample


# Import the agent you want to test
from streamlit_santa_agent.backend import SantaClausAgent

logger = logging.getLogger(__name__)

# Initialize phospho in backtest mode
os.environ["PHOSPHO_EXECUTION_MODE"] = "backtest"
phospho.init(project_id="jRg9zVIXRTqmokv84wSt")

# Collect evaluation
EVALUATION_RESULTS: Dict[str, int] = defaultdict(int)
COMPARISONS = []

# We'll do the evaluation with OpenAI
openai_client = OpenAI()


def evaluation_function(
    context: str,
    old_output_str: str,
    new_output: Any,
):
    """This is a simple evaluation function that calls OpenAI
    and asks which answer is better"""

    # If generator, we need to extract the str from the output
    if isinstance(new_output, GeneratorType):
        full_resp = ""
        for response in new_output:
            full_resp += response or ""
        new_output_str = phospho.extractor.detect_str_from_output(full_resp)
    else:
        new_output_str = phospho.extractor.detect_str_from_output(new_output)

    COMPARISONS.append({"input": context, "old": old_output_str, "new": new_output_str})

    prompt = f"""Chose which of the response is better as an answer to the following context:
---
Context: {context}
---
Response A: {old_output_str}
---
Response B: {new_output_str}
----

Possible answers:
Choice A: Response A is better
Choice B: Response B is better
Choice C: Both are equally good
Choice D: Both are equally bad

Choice: """

    response = openai_client.chat.completions.create(
        messages=[{"role": "system", "content": prompt}],
        model="gpt-3.5-turbo",
        max_tokens=2,
    )
    text_response = response.choices[0].message.content
    # Map back 'Choice A' to 'Response A is better' etc.
    mapping = {
        "Choice A": "Old output is better",
        "Choice B": "New output is better",
        "Choice C": "Same quality",
        "Choice D": "Both are bad",
    }

    EVALUATION_RESULTS[mapping[text_response]] += 1


def evaluate_a_task(task):
    """This function evaluates a single task"""

    try:
        print("Task id: ", task.id)
        santa_claus_agent = SantaClausAgent()
        new_output = santa_claus_agent.answer(**task.content["additional_input"])
        # Compare
        evaluation_function(
            task.content["input"],
            task.content["output"],
            new_output,
        )
    except Exception as e:
        logger.error(f"Error while answering task {task.id}: {e}")


def main():
    # Pull the logs from phospho
    tasks = phospho.client.tasks.get_all()
    if len(tasks) > 10:
        tasks = sample(tasks, 10)

    with concurrent.futures.ThreadPoolExecutor() as executor:
        # Submit tasks to the executor
        executor.map(evaluate_a_task, tasks)

    pprint(COMPARISONS)
    print(EVALUATION_RESULTS)


if __name__ == "__main__":
    main()
