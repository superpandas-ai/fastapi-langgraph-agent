"""This file contains the chat schema for the application."""

import re
from typing import (
    Any,
    List,
    Literal,
    Optional,
)

from pydantic import (
    BaseModel,
    Field,
    field_validator,
)


class Message(BaseModel):
    """Message model for chat endpoint.

    Attributes:
        role: The role of the message sender (user or assistant).
        content: The content of the message.
    """

    model_config = {"extra": "ignore"}

    role: Literal["user", "assistant",
                  "system"] = Field(..., description="The role of the message sender")
    content: str = Field(..., description="The content of the message",
                         min_length=1, max_length=12000)

    @field_validator("content")
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate the message content.

        Args:
            v: The content to validate

        Returns:
            str: The validated content

        Raises:
            ValueError: If the content contains disallowed patterns
        """
        # Check for potentially harmful content
        if re.search(r"<script.*?>.*?</script>", v, re.IGNORECASE | re.DOTALL):
            raise ValueError(
                "Content contains potentially harmful script tags")

        # Check for null bytes
        if "\0" in v:
            raise ValueError("Content contains null bytes")

        return v


class ChatRequest(BaseModel):
    """Request model for chat endpoint.

    Attributes:
        messages: List of messages in the conversation.
    """

    messages: List[Message] = Field(
        ...,
        description="List of messages in the conversation",
        min_length=1,
    )

    platform: Optional[Literal["fic", "sevdesk", "hr"]] = Field(
        None,
        description="The platform to use for the chat",
    )


class ChatResponse(BaseModel):
    """Response model for chat endpoint.

    Attributes:
        messages: List of messages in the conversation.
        generated_code: The generated code to answer the user's question.
        fig: The figure for plotting the data.
    """

    messages: List[Message] = Field(...,
                                    description="List of messages in the conversation")

    generated_code: Optional[str] = Field(
        None,
        description="The generated code to answer the user's question.",
    )

    fig: Optional[Any] = Field(
        None,
        description="The figure for plotting the data.",
    )


class StreamResponse(BaseModel):
    """Response model for streaming chat endpoint.

    Attributes:
        content: The content of the current chunk.
        done: Whether the stream is complete.
    """

    content: str = Field(
        default="", description="The content of the current chunk")
    done: bool = Field(
        default=False, description="Whether the stream is complete")


class AgentSelection(BaseModel):
    """Request model for agent selection endpoint.

    Attributes:
        platform: The platform to select for the session.
    """

    platform: Literal["fic", "sevdesk", "hr"] = Field(
        ...,
        description="The platform to select for the session",
    )
