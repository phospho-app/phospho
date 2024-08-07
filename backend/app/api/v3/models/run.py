from pydantic import BaseModel, Field
from typing import List


class Message(BaseModel, extra="allow"):
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


class RunBacktestRequest(BaseModel):
    project_id: str = Field(..., description="The phospho project_id")
    system_prompt_template: str = Field(..., description="The system prompt template")
    system_prompt_variables: dict = Field(
        ..., description="The system prompt variables"
    )
    provider_and_model: str = Field(..., description="The provider and model")
    version_id: str = Field(..., description="The version id")
