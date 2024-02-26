from pydantic import BaseModel, Field
from phospho.utils import generate_timestamp, generate_uuid
from typing import Any, Optional, List
from enum import Enum


class Message(BaseModel):
    id: str = Field(default_factory=generate_uuid)
    created_at: int = Field(default_factory=generate_timestamp)
    role: Optional[str] = None
    content: str
    previous_messages: List["Message"] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)

    def transcript(
        self,
        with_role: bool = True,
        with_previous_messages: bool = False,
        only_previous_messages: bool = False,
    ) -> str:
        """
        Return a string representation of the message.
        """
        transcript = ""
        if with_previous_messages:
            transcript += "\n".join(
                [
                    message.transcript(with_role=with_role)
                    for message in self.previous_messages
                ]
            )
        if not only_previous_messages:
            if with_role:
                transcript += f"{self.role}: {self.content}"
            else:
                transcript += "\n" + self.content
        return transcript

    def previous_messages_transcript(
        self,
        with_role: bool = True,
    ) -> Optional[str]:
        """
        Return a string representation of the message.
        """
        if len(self.previous_messages) == 0:
            return None
        return self.transcript(
            with_role=with_role,
            with_previous_messages=True,
            only_previous_messages=True,
        )

    def latest_interaction(self) -> str:
        """
        Return the latest interaction of the message
        """
        # Latest interaction is the last message of the previous messages
        # And the message itself
        if len(self.previous_messages) == 0:
            return self.transcript(with_role=True)
        else:
            return "\n".join(
                [
                    self.previous_messages[-1].transcript(with_role=True),
                    self.transcript(with_role=True),
                ]
            )

    def latest_interaction_context(self) -> Optional[str]:
        """
        Return the context of the latest interaction, aka
        the n-2 previous messages until n-1 and message.
        """
        if len(self.previous_messages) <= 1:
            return None
        else:
            return "\n".join(
                [
                    message.transcript(with_role=True)
                    for message in self.previous_messages[:-1]
                ]
            )


class ResultType(Enum):
    error = "error"
    bool = "bool"
    literal = "literal"


class JobResult(BaseModel):
    created_at: int = Field(default_factory=generate_timestamp)
    job_id: str
    result_type: ResultType
    value: Any
    logs: List[Any] = Field(default_factory=list)
    metadata: dict = Field(default_factory=dict)
