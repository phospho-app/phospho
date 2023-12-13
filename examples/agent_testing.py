"""
This is an example of how to backtest an agent with phospho
"""
import phospho
from openai import OpenAI
from collections import defaultdict

from streamlit_santa_agent.backend import SantaClausAgent
from dotenv import load_dotenv

load_dotenv()

phospho.init()
openai_client = OpenAI()

# Load the agent
santa_claus_agent = SantaClausAgent()

EVALUATION_RESULTS = defaultdict(int)


def evaluation_function(
    context: str,
    old_output: str,
    new_output: str,
):
    """This is a simple evaluation function that calls OpenAI
    and asks which answer is better"""
    prompt = f"""Chose which of the response is better as an answer to the following context:
---
Context: {context}
---
Response A: {old_output}
---
Response B: {new_output}
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
        max_tokens=1,
    )
    EVALUATION_RESULTS[response.choices[0].text] += 1


# Pull the logs from phospho
tasks = phospho.client.tasks.get_all()

for task in tasks:
    new_output = santa_claus_agent.answer(**task.content["raw_input"])

    # Compare
    evaluation_function(
        task.content["input"],
        task.content["raw_output"],
        new_output,
    )
