import json

import phospho
import requests

# from dotenv import load_dotenv

# load_dotenv()

phospho.init(api_key="test", project_id="test", tick=0.5)

# NOTE: ollama must be running for this to work, start the ollama app or run `ollama serve`
model = "zephyr"  # TODO: update this for whatever model you wish to use


def generate(prompt, context):
    r = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model,
            "prompt": prompt,
            "context": context,
        },
        stream=True,
    )
    r.raise_for_status()
    response_iterator = r.iter_lines()

    # In order to directly log this to phospho, we need to wrap it this way
    response_iterator = phospho.MutableGenerator(
        generator=response_iterator,
        # we need to indicate when the generation stops
        stop=lambda line: json.loads(line).get("done", False),
    )
    # the generated content will be logged to phospho
    phospho.log(input=prompt, output=response_iterator, stream=True)

    for line in response_iterator:
        body = json.loads(line)
        response_part = body.get("response", "")
        # the response streams one token at a time, print that as we receive it
        print(response_part, end="", flush=True)

        if "error" in body:
            raise Exception(body["error"])

        if body.get("done", False):
            # Say that the translation is finished
            return body["context"]


def main():
    context = []  # the context stores a conversation history, you can use this to make the model more context aware
    while True:
        user_input = input("Enter a prompt: ")
        print()
        context = generate(user_input, context)
        print()


if __name__ == "__main__":
    main()
