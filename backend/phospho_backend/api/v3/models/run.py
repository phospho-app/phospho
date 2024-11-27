from phospho.models import ProjectDataFilters
from phospho.utils import generate_version_id
from pydantic import BaseModel, Field


class RoleContentMessage(BaseModel, extra="allow"):
    """
    A message with a role and content.

    Extras fields are allowed, but ignored.
    """

    role: str = Field(..., examples=["user", "assistant", "system"])
    content: str


class RunPipelineOnMessagesRequest(BaseModel):
    """
    Process a conversation of messages.
    """

    project_id: str = Field(..., description="The phospho project_id")
    messages: list[RoleContentMessage] = Field(
        default_factory=list,
        description="Ordered and continuous messages in a single session. Similar to the OpenAI api.",
    )


class RunBacktestRequest(BaseModel):
    project_id: str = Field(description="The phospho project_id")
    system_prompt_template: str = Field(
        description=r"The system prompt template. Templated variables can be passed in the format of \{variable\}.",
    )
    system_prompt_variables: dict | None = Field(
        None, description="The system prompt variables as a dictionary."
    )
    provider_and_model: str = Field(
        description="The provider and model slug that will be used for the backtest.",
        examples=["openai:gpt-3.5-turbo", "mistral:mistral-small"],
    )
    version_id: str = Field(
        default_factory=generate_version_id,
        description="A nickname for the candidate version, currently testing.",
    )
    filters: ProjectDataFilters | None = Field(
        None,
        description="The filters to be applied to the project data. If None, no filters are applied.",
    )
