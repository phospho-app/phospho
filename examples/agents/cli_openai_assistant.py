"""
This is an example minimal assistant in the console which logs interactions to phospho.

## Setup 

Create `.env` file:
```
PHOSPHO_PROJECT_ID=...
PHOSPHO_API_KEY=...
MISTRAL_API_KEY=...
```

Launch the script:
```
python cli_openai_assistant.py
```
"""
import phospho
from dotenv import load_dotenv

load_dotenv()

# By default, phospho will look for the PHOSPHO_PROJECT_ID and PHOSPHO_API_KEY environment variables
# All the chat.completions calls of the OpenAI module will be logged to phospho
phospho.init()
client = phospho.lab.get_sync_client("mistral")


messages = []

print("Ask GPT anything (Ctrl+C to quit)", end="")

while True:
    prompt = input("\n>")
    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        messages=messages,
        model="mistral-small",
        stream=True,
    )

    print("\nAssistant: ", end="")
    for r in response:
        text = r.choices[0].delta.content
        if text is not None:
            print(text, end="", flush=True)
