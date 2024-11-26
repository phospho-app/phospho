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

import phospho
import streamlit as st
from openai import OpenAI
from openai._streaming import Stream
from openai.types.chat import ChatCompletionChunk

st.title("Assistant")  # Let's do an LLM-powered assistant !

# Initialize phospho to collect logs
phospho.init(
    api_key=st.secrets["PHOSPHO_API_KEY"],
    project_id=st.secrets["PHOSPHO_PROJECT_ID"],
)

# We will use OpenAI
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# The messages between user and assistant are kept in the session_state (the browser's cache)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Initialize a session. A session is used to group interactions of a single chat
if "session_id" not in st.session_state:
    st.session_state.session_id = phospho.new_session()

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
            "model": "gpt-4o-mini",
            # messages contains the whole chat history
            "messages": [
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            # stream asks to return a Stream object
            "stream": True,
        }
        # The OpenAI module gives us back a stream object
        streaming_response: Stream[ChatCompletionChunk] = (
            client.chat.completions.create(**full_prompt)
        )

        # ----> this is how you log to phospho
        logged_content = phospho.log(
            input=full_prompt,
            output=streaming_response,
            # We use the session_id to group all the logs of a single chat
            session_id=st.session_state.session_id,
            # Adapt the logging to streaming content
            stream=True,
        )

        # When you iterate on the stream, you get a token for every response
        for response in streaming_response:
            full_str_response += response.choices[0].delta.content or ""
            message_placeholder.markdown(full_str_response + "▌")

        # If you don't want to log every streaming chunk, log only the final output.
        # phospho.log(input=full_prompt, output=full_str_response, metadata={"stuff": "other"})
        message_placeholder.markdown(full_str_response)

    st.session_state.messages.append(
        {"role": "assistant", "content": full_str_response}
    )
