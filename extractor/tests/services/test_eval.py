import os
import pytest
from app.services.eval import get_flag, evaluate_task

assert os.getenv("ENVIRONMENT") != "production"


@pytest.mark.asyncio
async def test_evals(db, populated_project):
    async for mongo_db in db:
        task_input = "What is the weather like today?"
        task_output = "The weather is sunny today."

        # Build zero shot prompt
        prompt = f"""
        Your are an impartial judge evaluating an interaction between a user and an assistant. 
        The assistant might have been helpful or not. 
        Your goal is to determine if the assistant was helpful or not to the user.

        Here is the interaction between the user and the assistant:
        [START INTERACTION]
        User: {task_input}
        Assistant: {task_output}
        [END INTERACTION]

        Respond with only one word, success if the assistant was helpful, failure if not.
        """

        flag = await get_flag(prompt)

        assert flag in ["success", "failure"]

        task_input = "What is the weather like today?"
        task_output = "The weather is sunny today."

        # Build zero shot prompt
        prompt = f"""
        Your are an impartial judge evaluating an interaction between a user and an assistant. 
        The assistant might have been helpful or not. 
        Your goal is to determine if the assistant was helpful or not to the user.

        Here is the interaction between the user and the assistant:
        [START INTERACTION]
        User: {task_input}
        Assistant: {task_output}
        [END INTERACTION]

        Respond with only one word, success if the assistant was helpful, failure if not.
        """

        flag = await get_flag(prompt, model_name="gpt-4o")

        assert flag in ["success", "failure"]

        task_input = "What is the weather like today?"
        task_output = "The weather is sunny today."

        flag = await evaluate_task(task_input, task_output)

        assert flag in ["success", "failure"]

        previous_task_input = "What is the weather like today?"
        previous_task_output = "The weather is sunny today."
        task_input = "And tomorow?"
        task_output = "It will be rainy."

        flag = await evaluate_task(
            task_input,
            task_output,
            previous_task_input=previous_task_input,
            previous_task_output=previous_task_output,
        )

        assert flag == "success"

        # Not enough examples case
        successful_examples = [
            {
                "input": "What is the weather like today?",
                "output": "The weather is sunny today.",
                "flag": "success",
            }
        ]
        unsuccessful_examples = [
            {
                "input": "What is the weather like today?",
                "output": "I have no idea",
                "flag": "failure",
            }
        ]

        flag = await evaluate_task(
            task_input,
            task_output,
            successful_examples=successful_examples,
            unsuccessful_examples=unsuccessful_examples,
        )
        assert flag in ["success", "failure"]

        flag = await evaluate_task(
            task_input, task_output, successful_examples=successful_examples
        )
        assert flag in ["success", "failure"]

        # Successful Examples
        successful_examples = [
            {
                "input": "What is the weather like today?",
                "output": "The weather is sunny today.",
                "flag": "success",
            },
            {
                "input": "Will it rain tomorrow?",
                "output": "There is a high chance of rain tomorrow.",
                "flag": "success",
            },
            {
                "input": "Is it cold outside right now?",
                "output": "The temperature is quite low, so it's cold outside.",
                "flag": "success",
            },
            {
                "input": "Do I need an umbrella today?",
                "output": "No, it's not expected to rain today.",
                "flag": "success",
            },
            {
                "input": "How's the weather this weekend?",
                "output": "The weather this weekend will be warm and sunny.",
                "flag": "success",
            },
        ]

        # Unsuccessful Examples
        unsuccessful_examples = [
            {
                "input": "What is the weather like today?",
                "output": "I am not sure about today's movies.",
                "flag": "failure",
            },
            {
                "input": "Will it rain tomorrow?",
                "output": "Tomorrow's weather is not available right now.",
                "flag": "failure",
            },
            {
                "input": "Is it cold outside right now?",
                "output": "The best restaurants are downtown.",
                "flag": "failure",
            },
            {
                "input": "Do I need an umbrella today?",
                "output": "Umbrellas are sold at the nearby store.",
                "flag": "failure",
            },
            {
                "input": "How's the weather this weekend?",
                "output": "This weekend there is a music festival.",
                "flag": "failure",
            },
        ]

        input = "What is the weather like today?"
        output = "The weather is sunny today."

        flag = await evaluate_task(
            input,
            output,
            successful_examples=successful_examples,
            unsuccessful_examples=unsuccessful_examples,
        )

        assert flag == "success"

        # Error case
        input = "What is the weather like today?"
        output = "I don't have access to real time data."

        flag = await evaluate_task(
            input,
            output,
            successful_examples=successful_examples,
            unsuccessful_examples=unsuccessful_examples,
        )

        assert flag == "failure"

        # Successful Examples
        successful_examples = [
            {
                "input": "What is the weather like today?",
                "output": "The weather is sunny today.",
                "flag": "success",
            },
            {
                "input": "Will it rain tomorrow?",
                "output": "There is a high chance of rain tomorrow.",
                "flag": "success",
            },
            {
                "input": "Is it cold outside right now?",
                "output": "The temperature is quite low, so it's cold outside.",
                "flag": "success",
            },
            {
                "input": "Do I need an umbrella today?",
                "output": "No, it's not expected to rain today.",
                "flag": "success",
            },
            {
                "input": "How's the weather this weekend?",
                "output": "The weather this weekend will be warm and sunny.",
                "flag": "success",
            },
        ]

        # Unsuccessful Examples
        unsuccessful_examples = [
            {
                "input": "What is the weather like today?",
                "output": "I am not sure about today's movies.",
                "flag": "failure",
            },
            {
                "input": "Will it rain tomorrow?",
                "output": "Tomorrow's weather is not available right now.",
                "flag": "failure",
            },
            {
                "input": "Is it cold outside right now?",
                "output": "The best restaurants are downtown.",
                "flag": "failure",
            },
            {
                "input": "Do I need an umbrella today?",
                "output": "Umbrellas are sold at the nearby store.",
                "flag": "failure",
            },
            {
                "input": "How's the weather this weekend?",
                "output": "This weekend there is a music festival.",
                "flag": "failure",
            },
        ]

        input = "What is the weather like today?"
        output = "The weather is sunny today."

        # Make a loop to create a 100 examples list
        successful_examples_100 = []
        unsuccessful_examples_100 = []

        for i in range(100):
            successful_examples_100.append(successful_examples[0])
            unsuccessful_examples_100.append(unsuccessful_examples[0])

        flag = await evaluate_task(
            input,
            output,
            successful_examples=successful_examples_100,
            unsuccessful_examples=unsuccessful_examples,
        )

        assert flag in ["success", "failure"]

        flag = await evaluate_task(
            input,
            output,
            successful_examples=successful_examples,
            unsuccessful_examples=unsuccessful_examples_100,
        )

        assert flag in ["success", "failure"]

        flag = await evaluate_task(
            input,
            output,
            successful_examples=successful_examples_100,
            unsuccessful_examples=unsuccessful_examples_100,
        )

        assert flag in ["success", "failure"]
