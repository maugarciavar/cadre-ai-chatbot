from typing import Literal

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    """One turn in a conversation."""

    role: Literal["user", "assistant"] = Field(description="Who sent this message.")
    content: str = Field(description="The message text.")


class ChatRequest(BaseModel):
    """A request to /api/chat."""

    message: str = Field(description="The new user message to answer.")
    history: list[ChatMessage] = Field(
        default_factory=list,
        description=(
            "Prior turns in the conversation, oldest first. Do not include "
            "`message` itself -- the server appends it as the final user turn."
        ),
    )


class ChatResult(BaseModel):
    """Structured model output. Also doubles as the /api/chat response body."""

    reply: str = Field(description="The assistant's reply, grounded in Cadre AI's curated knowledge.")
    escalate: bool = Field(
        description=(
            "True if a human should also follow up (e.g. to give a specific "
            "quote). Not a failure signal -- `reply` is still a complete "
            "answer either way."
        )
    )


class HealthStatus(BaseModel):
    """Response body for /api/health."""

    status: str = Field(description="Always \"ok\" when the service is reachable.")
