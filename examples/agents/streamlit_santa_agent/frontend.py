import streamlit as st
from streamlit_feedback import streamlit_feedback

from backend import SantaClausAgent

# Let's do an LLM-powered Santa Claus agent !
santa_claus_agent = SantaClausAgent()
avatars = {"user": "🐸", "assistant": "🎅🏼"}

# Let's dress up...
st.title("🎄🎅🏼 Santa ChatBot")
left, right = st.columns(2)
with left:
    if st.button("New chat"):
        st.session_state.session_id = santa_claus_agent.new_session()
        st.session_state.messages = []
with right:
    st.write("Have a conversation with Santa!")


# The messages between user and assistant are kept in the session_state (the local storage)
if "messages" not in st.session_state:
    st.session_state.messages = []

# Start a session. A session is used to group interactions of a single chat
if "session_id" not in st.session_state:
    st.session_state.session_id = santa_claus_agent.new_session()


# Fetch the first message and display it word by word
if st.session_state.messages == []:
    with st.chat_message("assistant", avatar=avatars["assistant"]):
        message_placeholder = st.empty()
        for streamed_content in santa_claus_agent.random_intro(
            session_id=st.session_state.session_id
        ):
            message_placeholder.markdown(streamed_content + "▌")
        message_placeholder.markdown(streamed_content)
        st.session_state.messages = [{"role": "assistant", "content": streamed_content}]
else:
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"], avatar=avatars[message["role"]]):
            st.markdown(message["content"])


# This is the user's textbox for chatting with the assistant
if prompt := st.chat_input("All I want for Christmas is..."):
    generation_finished = False

    # When the user sends a message...
    new_message = {"role": "user", "content": prompt}
    st.session_state.messages.append(new_message)
    with st.chat_message("user", avatar=avatars["user"]):
        st.markdown(prompt)

    # ... the assistant replies
    with st.chat_message("assistant", avatar=avatars["assistant"]):
        message_placeholder = st.empty()
        full_str_response = ""
        # We ask the Santa Claus agent to respond token by token
        streamed_response = santa_claus_agent.answer(
            messages=st.session_state.messages, session_id=st.session_state.session_id
        )
        for resp in streamed_response:
            full_str_response += resp or ""
            message_placeholder.markdown(full_str_response + "▌")
        message_placeholder.markdown(full_str_response)
        generation_finished = True
    # We update the local storage
    st.session_state.messages.append(
        {"role": "assistant", "content": full_str_response}
    )

# Let's collect some feedback from the user


def _submit_feedback(feedback: dict):
    santa_claus_agent.feedback(raw_flag=feedback["score"], notes=feedback["text"])
    st.toast("Thank you for your feedback!🎅🏼")


if len(st.session_state.messages) > 1:
    feedback = streamlit_feedback(
        feedback_type="thumbs",
        optional_text_label="[Optional] Please provide an explanation",
        on_submit=_submit_feedback,
        # To create a new feedback component for every message and session, you need to provide a unique key
        key=f"{st.session_state.session_id}_{len(st.session_state.messages)}",
    )
