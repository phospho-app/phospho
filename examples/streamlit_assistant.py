"""
# Streamlit webapp with an OpenAI chatbot

This is a demo webapp that showcase a simple assistant agent whose response are logged to phospho.

## Setup

1. Create a secrets file examples/.streamlit/secrets.toml with your OpenAI API key
```
OPENAI_API_KEY="sk-..." # your actual key
```

2. Launch the webapp
```
cd examples/ 
streamlit run webapp.py
```

"""

import streamlit as st
import phospho
from openai import OpenAI
from openai.types.chat import ChatCompletionChunk
from openai._streaming import Stream


st.title("Assistant")  # Let's do an LLM-powered assistant !

# Initialize phospho to collect logs
phospho.init(
    api_key=st.secrets["PHOSPHO_API_KEY"],
    project_id=st.secrets["PHOSPHO_PROJECT_ID"],
)
phospho.config.BASE_URL = "https://phospho-backend-zxs3h5fuba-ew.a.run.app/v0"

# We will use OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# The messages between user and assistant are kept in the session_state (the browser's cache)
if "messages" not in st.session_state:
    st.session_state.messages = []
# Messages are displayed the following way
for message in st.session_state.messages:
    with st.chat_message(name=message["role"]):
        st.markdown(message["content"])

# This is the user's textbox for chatting with the assistant
if prompt := st.chat_input("What is up?"):
    # When the user sends a message...
    new_message = {"role": "user", "content": prompt}
    st.session_state.messages.append(new_message)
    with st.chat_message("user"):
        st.markdown(prompt)

    # ... the assistant replies
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        full_str_response = ""
        # We build a query to OpenAI
        full_prompt = {
            "model": "gpt-3.5-turbo",
            # messages contains the whole chat history
            "messages": [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            # stream asks to return a Stream object
            "stream": True,
        }
        # The OpenAI module gives us back a stream object
        streaming_response: Stream[
            ChatCompletionChunk
        ] = client.chat.completions.create(**full_prompt)
        # When you iterate on the stream, you get a token for every response
        for response in streaming_response:
            # We can log each individual response in phospho
            # phospho takes care of aggregating all of the tokens into a single, sensible log.
            # It's battery-included.
            # phospho will log all the parameters and all the responses, which is great for debugging
            logged_content = phospho.log(input=full_prompt, output=response)

            # We ask streamlit to display the output of the logged_content.
            # This is equivalent to:
            # full_str_response += response.choices[0].delta.content or ""
            full_str_response = logged_content["output"] or ""

            message_placeholder.markdown(full_str_response + "▌")

        # If you don't want to log every streaming chunk (too much data ?)
        # you can simply log the final output.
        # phospho logging is meant to be flexible.
        # phospho.log(input=full_prompt, output=full_str_response, metadata={"stuff": "other"})
        message_placeholder.markdown(full_str_response)

    st.session_state.messages.append(
        {"role": "assistant", "content": full_str_response}
    )
