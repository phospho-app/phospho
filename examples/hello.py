import phospho
import openai

phospho.init()
openai_client = openai.OpenAI()

query = {
    "messages": [{"role": "user", "content": "Say hi !"}],
    "model": "gpt-3.5-turbo",
}
response = openai_client.chat.completions.create(**query)

phospho.log(input=query, output=response)
