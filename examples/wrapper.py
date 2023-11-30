"""
This is an example minimal assistant in the console which logs interactions to phospho.

It demonstrates how to use `phospho.wrap()` with streaming content.

## Setup 

Create `.env` file:
```
PHOSPHO_PROJECT_ID=...
PHOSPHO_API_KEY=...
OPENAI_API_KEY=...
```

Launch the script:
```
python wrapper.py
```
"""

import phospho
import openai

from dotenv import load_dotenv

load_dotenv()

phospho.init()
openai_client = openai.OpenAI()

messages = []

print("Ask GPT anything (Ctrl+C to quit)", end="")

while True:
    prompt = input("\n>")
    messages.append({"role": "user", "content": prompt})

    query = {
        "messages": messages,
        "model": "gpt-3.5-turbo",
        "stream": True,
    }
    response = openai_client.chat.completions.create(**query)

    phospho.log(input=query, output=response, stream=True)

    print("\nAssistant: ", end="")
    for r in response:
        text = r.choices[0].delta.content
        if text is not None:
            print(text, end="", flush=True)
