"""
A script to populate a project with some data
"""

import os
from typing import List

import phospho
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv("../backend/.env")

assert (
    os.getenv("OPENAI_API_KEY") is not None
), "Please set the OPENAI_API_KEY environment variable"
assert (
    os.getenv("PHOSPHO_TEST_API_KEY") is not None
), "Please set the PHOSPHO_TEST_API_KEY environment variable"
assert (
    os.getenv("PHOSPHO_TEST_PROJECT_ID") is not None
), "Please set the PHOSPHO_TEST_PROJECT_ID environment variable"


phospho.init(
    api_key=os.getenv("PHOSPHO_TEST_API_KEY"),
    project_id=os.getenv("PHOSPHO_TEST_PROJECT_ID"),
    base_url="http://127.0.0.1:8000/v2",
    raise_error_on_fail_to_send=True,
)

user_inputs: List[str] = ["What is the price of the Suziki?"]
assistant_outputs: List[str] = ["The price of the motorbike is $20,000"]

openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

NB_OF_QUESTIONS_TO_ASK = 20
print(f"generating {NB_OF_QUESTIONS_TO_ASK} input output pairs...")


def generate_user_question(user_inputs: List[str]) -> str:
    system_prompt = "You are customer in a motorbikes dealership, talking to a salesperson. You cannot ask the following questions: "
    for user_input in user_inputs:
        system_prompt += f"{user_input}, "

    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": system_prompt},
            {
                "role": "user",
                "content": "Generate a question that I can ask the salesperson. Only answer with the question to tthe salesperson.",
            },
        ],
    )

    if response.choices[0].message.content:
        return response.choices[0].message.content
    else:
        return "I don't know what to ask"


for i in range(NB_OF_QUESTIONS_TO_ASK):
    user_question = generate_user_question(user_inputs)
    print(f"user: {user_question}")
    user_inputs.append(user_question)

    # Get the assistant response
    response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a salesperson in a motorbikes dealership. You are talking to a customer. Be concise.",
            },
            {
                "role": "user",
                "content": user_question,
            },
        ],
        max_tokens=75,
    )

    assistant_response = response.choices[0].message.content
    print(f"assistant: {assistant_response}")

    if assistant_response:
        assistant_outputs.append(assistant_response)
    else:
        raise Exception("Assistant response is None")

    phospho.log(
        input=user_question,
        output=assistant_response,
    )
