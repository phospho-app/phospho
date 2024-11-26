import asyncio
import os
import random
from typing import Any, AsyncGenerator, Dict, List

import phospho
import pydantic
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from openai import AsyncOpenAI, OpenAIError
from openai.types.chat import ChatCompletionChunk

# This is an example implementation of a FastAPI backend of an LLM app,
# where interactions are logged with phospho

app = FastAPI()

load_dotenv()

phospho_api_key = os.getenv("PHOSPHO_API_KEY")
phospho_project_id = os.getenv("PHOSPHO_PROJECT_ID")
phospho.init(api_key=phospho_api_key, project_id=phospho_project_id, tick=2)


# Agent implementation


class SantaClausAgent:
    """This agent talks with the end user. It uses an LLM to generate texts."""

    # This system prompt gives its personality to the agent
    system_prompt = [
        {
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
    ]

    def __init__(self, openai_client: AsyncOpenAI):
        self.openai_client = openai_client

    async def random_intro(self, session_id: str) -> AsyncGenerator[str, Any]:
        """This is used to greet the user when they log in"""
        # For additional personalisation, we also want to have prewritten answers.
        # LLM apps can combine LLM with traditional techniques to create awesome agents.
        chosen_intro = random.choice(
            [
                "Ho, ho, ho! Hello, little one! How are you today? Excited for Christmas?",
                "Jingle bells, jingle bells! Tell me! Have you been nice this years?",
                "Ho, ho! It's freezing out here! Quick! Tell me what you want for Christmas, before I turn into an ice cream!",
                "Hmm hmmm... Look who's here... Hello, you! Would you like to tell something to Santa?",
                "Ho, ho, ho! A penguin just ate my lunch-ho! And you, little one, how are you today?",
                "Hello my dear! Christmas is near, I hope you've been nice this year... Have you?",
                "Jingle bells! It's-a-me, Santa Claus from Kentucky! Yeeeeee-haa!",
                "Happy halloween!... Uh-oh. Wrong holidays! Ho, ho, ho! Merry Christmas, how are you?",
            ]
        )
        # Let's log this intro to phospho in order to see which one is the most engaging
        phospho.log(input="intro", output=chosen_intro, session_id=session_id)

        # Create a streaming effect
        splitted_text = chosen_intro.split(" ")

        for i, word in enumerate(splitted_text):
            partial_text = splitted_text[i] + " "
            yield partial_text
            await asyncio.sleep(0.05)

    async def answer(
        self, messages: List[Dict[str, str]], session_id: str
    ) -> AsyncGenerator[str, Any]:
        """This methods generates a response to the user in the character of Santa Claus.
        This text is displayed word by word, as soon as they are generated.

        This function returns a generator of a string, which is the text of the reply.

        In an API, this would return a stream response.
        """

        # To log this stream, we'll use phospho.wrap
        streaming_response: AsyncGenerator[ChatCompletionChunk, None] = phospho.wrap(
            self.openai_client.chat.completions.create,
            session_id=session_id,
        )(
            model="gpt-3.5-turbo",
            # messages contains:
            #  1. The system promptthe whole chat history
            #  2. The chat history
            #  3. The latest user request
            messages=self.system_prompt
            + [{"role": m["role"], "content": m["content"]} for m in messages],
            # stream asks to return a Stream object
            stream=True,
        )

        # When you iterate on the stream, you get a token for every response
        async for response in streaming_response:
            content = response.choices[0].delta.content
            if content is not None:
                yield content

    def new_session(self) -> str:
        """
        Start a new session. This is used to keep discussions separate in phospho.
        Returns the new session_id
        """
        return phospho.new_session()


# Resource shared between endpoints


def get_agent():
    openai_api_key = os.getenv("OPENAI_API_KEY")
    # It's important to use an AsyncOpenAI client so that streaming works properly
    openai_client = AsyncOpenAI(api_key=openai_api_key)
    agent = SantaClausAgent(openai_client=openai_client)
    return agent


# API endpoints


@app.get("/session-id")
def new_session_id(agent: SantaClausAgent = Depends(get_agent)) -> str:
    """Start a new session_id. This is used to keep discussions separate in phospho."""
    return agent.new_session()


@app.get("/random-intro")
async def random_intro(
    session_id: str, agent: SantaClausAgent = Depends(get_agent)
) -> StreamingResponse:
    return StreamingResponse(
        agent.random_intro(session_id=session_id), media_type="application/x-ndjson"
    )


class QueryAnswerModel(pydantic.BaseModel):
    messages: List[Dict[str, str]]
    session_id: str


@app.post("/answer")
async def answer(
    query: QueryAnswerModel,
    agent: SantaClausAgent = Depends(get_agent),
) -> StreamingResponse:
    try:
        return StreamingResponse(
            agent.answer(messages=query.messages, session_id=query.session_id),
            media_type="application/x-ndjson",
        )
    except OpenAIError:
        raise HTTPException(status_code=500, detail="OpenAI call failed")
