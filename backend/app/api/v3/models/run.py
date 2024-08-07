from phospho.models import ProjectDataFilters
from pydantic import BaseModel, Field
from typing import List, Optional


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
    system_prompt_template: str = Field(
        ...,
        description="The system prompt template. The templated variables are in the format of \{variable\}.",
    )
    system_prompt_variables: dict = Field(
        ..., description="The system prompt variables as a dictionary."
    )
    provider_and_model: str = Field(
        ...,
        description="The provider and model slug that will be used for the backtest.",
        examples=["openai:gpt-3.5-turbo", "mistral:mistral-small"],
    )
    version_id: str = Field(..., description="The version id to be tested.")
    filters: Optional[ProjectDataFilters] = Field(
        None,
        description="The filters to be applied to the project data. If None, no filters are applied.",
    )
