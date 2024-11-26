from typing import Dict, List

import requests
import streamlit as st

# Let's do an LLM-powered Santa Claus agent !
avatars = {"user": "🐸", "assistant": "🎅🏼"}


class Client:
    """This client connects to the local FastAPI backend"""

    BASE_URL = "http://localhost:8000"

    def session_id(self) -> str:
        return requests.get(self.BASE_URL + "/session-id").content.decode("utf-8")

    def random_intro(self, session_id: str) -> requests.Response:
        return requests.get(
            self.BASE_URL + "/random-intro",
            params={"session_id": session_id},
            stream=True,
        )

    def answer(
        self, messages: List[Dict[str, str]], session_id: str
    ) -> requests.Response:
        return requests.post(
            self.BASE_URL + "/answer",
            json={"messages": messages, "session_id": session_id},
            stream=True,
        )


# Connect to the local backend
client = Client()

# Start a session. A session is used to group interactions of a single chat
if "session_id" not in st.session_state:
    st.session_state.session_id = client.session_id()


# Let's dress up...
st.title("🎄🎅🏼 Santa ChatBot")
left, right = st.columns(2)
with left:
    if st.button("New chat"):
        # New chat = new session
        st.session_state.session_id = client.session_id()
        st.session_state.messages = []
with right:
    st.write("Have a conversation with Santa!")


# The messages between user and assistant are kept in the session_state (the local storage)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Fetch the first message and display it word by word
if st.session_state.messages == []:
    with st.chat_message("assistant", avatar=avatars["assistant"]):
        message_placeholder = st.empty()
        with client.random_intro(st.session_state.session_id) as r:
            full_str_response = ""
            for streamed_content in r:
                full_str_response += streamed_content.decode()
                message_placeholder.markdown(full_str_response + "▌")
            message_placeholder.markdown(full_str_response)
        st.session_state.messages = [
            {"role": "assistant", "content": full_str_response}
        ]
else:
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=avatars[message["role"]]):
            st.markdown(message["content"])

# This is the user's textbox for chatting with the assistant
if prompt := st.chat_input("All I want for Christmas is..."):
    # When the user sends a message...
    new_message = {"role": "user", "content": prompt}
    st.session_state.messages.append(new_message)
    with st.chat_message("user", avatar=avatars["user"]):
        st.markdown(prompt)

    # ... the assistant replies
    with st.chat_message("assistant", avatar=avatars["assistant"]):
        message_placeholder = st.empty()
        full_str_response = ""
        # We ask the Santa Claus agent to respond

        with client.answer(
            messages=st.session_state.messages, session_id=st.session_state.session_id
        ) as streaming_response:
            full_str_response = ""
            for resp in streaming_response:
                full_str_response += resp.decode()
                message_placeholder.markdown(full_str_response + "▌")
            message_placeholder.markdown(full_str_response)

    # We update the local storage
    st.session_state.messages.append(
        {"role": "assistant", "content": full_str_response}
    )
