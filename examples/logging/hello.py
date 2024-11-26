from pprint import pprint

import openai
import phospho

phospho.init()
openai_client = openai.OpenAI()

query = {
    "messages": [{"role": "user", "content": "Say hi !"}],
    "model": "gpt-3.5-turbo",
}
response = openai_client.chat.completions.create(**query)
logged_content = phospho.log(input=query, output=response)

print("The following content has been logged to phospho:")
pprint(logged_content)
