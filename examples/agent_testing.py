"""
This is an example of how to backtest an agent with phospho
"""
import phospho
import logging
from openai import OpenAI
from collections import defaultdict
from pprint import pprint
from types import GeneratorType
from typing import Any
from random import sample


# Import the agent you want to test
from streamlit_santa_agent.backend import santa_claus_agent

logger = logging.getLogger(__name__)

# Initialize phospho in backtest mode
phospho.config.BACKTEST_MODE = True
phospho.init(project_id="jRg9zVIXRTqmokv84wSt")

# Collect evaluation
EVALUATION_RESULTS = defaultdict(int)
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
Choice C: Both are equal
Choice D: Neither are correct

Choice: """

    response = openai_client.chat.completions.create(
        messages=[{"role": "system", "content": prompt}],
        model="gpt-3.5-turbo",
        max_tokens=2,
    )
    EVALUATION_RESULTS[response.choices[0].message.content] += 1


# Pull the logs from phospho
tasks = phospho.client.tasks.get_all()


for task in tasks:
    try:
        print("Task id: ", task.id)
        new_output = santa_claus_agent.answer(**task.content["additional_input"])
        # Compare
        evaluation_function(
            task.content["input"],
            task.content["output"],
            new_output,
        )
    except Exception as e:
        logger.error(f"Error while answering task {task.id}: {e}")

pprint(COMPARISONS)
print(EVALUATION_RESULTS)
