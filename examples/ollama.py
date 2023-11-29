import phospho
import json
import requests

phospho.init(api_key="test", project_id="test", tick=0.1)

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

    request_id = phospho.generate_uuid()
    for line in r.iter_lines():
        body = json.loads(line)
        response_part = body.get("response", "")
        # the response streams one token at a time, print that as we receive it
        print(response_part, end="", flush=True)

        # Add a logging endpoint for every response_part
        phospho.log(
            input=prompt, output=response_part, task_id=request_id, to_log=False
        )

        if "error" in body:
            raise Exception(body["error"])

        if body.get("done", False):
            # Say that the translation is finished
            phospho.log(input=prompt, output=None, task_id=request_id, to_log=True)
            return body["context"]


def main():
    context = []  # the context stores a conversation history, you can use this to make the model more context aware
    while True:
        user_input = input("Enter a prompt: ")
        print()
        context = generate(user_input, context)
        print(phospho.log_queue.events)
        print()


if __name__ == "__main__":
    main()
