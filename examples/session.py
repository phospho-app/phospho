import phospho
import openai

from typing import Tuple, Dict, Any

phospho.init(tick=0.5)
openai_client = openai.OpenAI()


def make_agent_do_stuff() -> Tuple[Dict[str, Any], Dict[str, Any]]:
    query = {
        "messages": [{"role": "user", "content": "Say hi !"}],
        "model": "gpt-3.5-turbo",
    }
    response = openai_client.chat.completions.create(**query)

    return query, response


# By default, a new session id is created at the beginning
input, output = make_agent_do_stuff()
phospho_log = phospho.log(input=input, output=output)
print(
    f"No session_id were specified. Phospho created this one: {phospho_log['session_id']}"
)

# And by default new logs keep this same session_id
input, output = make_agent_do_stuff()
phospho_log = phospho.log(input=input, output=output)
print(f"Just like before, the session_id is still: {phospho_log['session_id']}")

# You can customize sessions by passing them as arguments to the logging function
new_session_id = phospho.generate_uuid()
input, output = make_agent_do_stuff()
phospho_log = phospho.log(input=input, output=output, session_id=new_session_id)
print(f"The new session_id is: {phospho_log['session_id']}")
