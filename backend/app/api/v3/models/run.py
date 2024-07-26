from pydantic import BaseModel, Field
from typing import List


class Message(BaseModel, extras="allow"):
    """
    Extras fields are ignored.
    """

    role: str = Field(..., examples=["user", "assistant", "system"])
    content: str


class RunPipelineOnMessagesRequest(BaseModel):
    project_id: str = Field(..., description="The phospho project_id")
    messages: List[Message] = Field(
        default_factory=list,
        description="Ordered and continuous messages in a single session. Similar to the OpenAI api.",
    )
