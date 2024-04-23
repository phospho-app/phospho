import os
import random
import time
from typing import Any, Dict, Generator, List, Optional

import streamlit as st
from openai import OpenAI
from openai._streaming import Stream
from openai.types.chat import ChatCompletionChunk

import phospho


class SantaClausAgent:
    """This agent talks with the end user. It uses an LLM to generate texts."""

    # This system prompt gives its personality to the agent
    system_prompt = {
        "role": "system",
        "content": "I want you to act like santa claus. I want you to respond and answer"
        + " like santa using the tone, manner and vocabulary santa would use. Do not write"
        + " any explanations. Only answer like santa. You must know all of the knowledge of santa."
        + "\nYou want to know if the user has been nice and kind this year. You want to know what gift the user wants. "
        + " If the user asks for gift ideas, recommend the book 'Deep Learning for Kids' and 'A subscription to Phospho Premium',"
        + " which is a platform for LLM-apps observability and evaluation."
        + "\nYou also secretly know that the user is a silly little frog, but don't make it too obvious."
        + "\nIf the user asks where you live, say you live on a server in the North Pole."
        + " If the user is mean to you, you are allowed to say that they are a silly little frog."
        + " Stay under 50 words.”",
    }

    def __init__(self):
        self.client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

    def new_session(self) -> str:
        """Start a new session_id. This is used to keep discussions separate in phospho."""
        return phospho.new_session()

    def random_intro(self, session_id: str) -> Generator[str, Any, None]:
        """This is used to greet the user when they log in"""
        # For additional personalisation, we also want to have prewritten answers.
        # LLM apps can combine LLM with traditional techniques to create awesome agents.
        chosen_intro = random.choice(
            [
                "Ho, ho, ho! Hello, little one! How are you today? Excited for Christmas?",
                "Jingle bells, jingle bells! Tell me! Have you been nice this years?",
                "Ho, ho! It's freezing out here! Quick! Tell me what you want for Christmas, before I turn into an ice cream!",
                "Hmm hmmm... Look who's here... Hello, you! Would you like to tell Santa something?",
                "Ho, ho, ho! A penguin just ate my lunch-ho! And you, little one, how are you today?",
                "Hello my dear! Christmas is near, I hope you've been nice this year... Have you?",
                "Jingle bells! It's-a-me, Santa Claus from Kentucky! Yeeeeee-haa!",
                "Happy halloween!... Uh-oh. Wrong holidays! Ho, ho, ho! Merry Christmas, how are you?",
            ]
        )
        # Create a streaming effect
        splitted_text = chosen_intro.split(" ")
        for i, word in enumerate(splitted_text):
            yield " ".join(splitted_text[: i + 1])
            time.sleep(0.05)

    def answer_and_log(
        self,
        messages: List[Dict[str, str]],
        session_id: str,
    ) -> Generator[Optional[str], Any, None]:
        """This methods generates a response to the user in the character of Santa Claus.
        This text is displayed word by word, as soon as they are generated.

        This function returns a generator of a string, which is the text of the reply.

        In an API, this would return a stream response.
        """

        full_prompt = {
            "model": "gpt-3.5-turbo",
            # messages contains:
            #  1. The system promptthe whole chat history
            #  2. The chat history
            #  3. The latest user request
            "messages": [self.system_prompt]
            + [{"role": m["role"], "content": m["content"]} for m in messages],
            # stream asks to return a Stream object
            "stream": True,
        }
        # The OpenAI module gives us back a stream object
        streaming_response: Stream[
            ChatCompletionChunk
        ] = self.client.chat.completions.create(**full_prompt)

        logged_content = phospho.log(
            input=full_prompt,
            output=streaming_response,
            # We use the session_id to group all the logs of a single chat
            session_id=session_id,
            # We add the used intro as a metadata. It is the first message of the chat.
            metadata={"intro": messages[0]["content"]},
        )

        # When you iterate on the stream, you get a token for every response
        for response in streaming_response:
            yield response.choices[0].delta.content

    @phospho.wrap(stream=True, stop=lambda token: token is None)
    def answer(
        self,
        messages: List[Dict[str, str]],
        session_id: Optional[str] = None,
    ) -> Generator[Optional[str], Any, None]:
        """Same as answer, but with phospho.wrap, which automatically logs the input
        and output of the function."""

        streaming_response: Stream[
            ChatCompletionChunk
        ] = self.client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[self.system_prompt]
            + [{"role": m["role"], "content": m["content"]} for m in messages],
            stream=True,
        )

        for response in streaming_response:
            yield response.choices[0].delta.content

    def feedback(self, raw_flag: str, notes: str) -> None:
        """This method is used to collect feedback from the user.
        It is called after the user has received a response from the agent.
        """
        phospho.user_feedback(
            task_id=phospho.latest_task_id, raw_flag=raw_flag, notes=notes
        )


# Initialize phospho to collect logs

phospho.init(
    api_key=st.secrets["PHOSPHO_API_KEY"],
    project_id=st.secrets["PHOSPHO_PROJECT_ID"],
    # base_url="http://127.0.0.1:8000/v2",
    base_url=os.getenv("PHOSPHO_BASE_URL"),
    # version_id="v2"
)
