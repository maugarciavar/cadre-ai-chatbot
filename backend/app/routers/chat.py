from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import ChatRequest, ChatResult
from app.services.openrouter_client import OpenRouterServiceError, get_chat_result

router = APIRouter()


@router.post(
    "/api/chat",
    response_model=ChatResult,
    summary="Send a chat message",
    description=(
        "Answers a message using Cadre AI's curated knowledge. Stateless -- "
        "send the full prior conversation as `history` with each request."
    ),
    responses={
        422: {
            "description": (
                "`message`, or a message in `history`, exceeds the configured "
                "character limit."
            ),
            "content": {
                "application/json": {
                    "example": {"detail": "Message exceeds the 2000 character limit."}
                }
            },
        },
        503: {
            "description": "The OpenRouter API call failed, timed out, or returned an unusable response.",
            "content": {
                "application/json": {
                    "example": {
                        "detail": "Cadre AI chatbot is temporarily unavailable. Please try again shortly."
                    }
                }
            },
        },
    },
)
def chat(request: ChatRequest) -> ChatResult:
    if len(request.message) > settings.max_message_length:
        raise HTTPException(
            status_code=422,
            detail=f"Message exceeds the {settings.max_message_length} character limit.",
        )

    # Keep only the most recent turns -- a simple cap, not token counting.
    history = request.history[-settings.max_history_messages :]

    if any(len(m.content) > settings.max_message_length for m in history):
        raise HTTPException(
            status_code=422,
            detail=f"A message in the conversation history exceeds the {settings.max_message_length} character limit.",
        )

    try:
        return get_chat_result(history=history, message=request.message)
    except OpenRouterServiceError as exc:
        raise HTTPException(
            status_code=503,
            detail="Cadre AI chatbot is temporarily unavailable. Please try again shortly.",
        ) from exc
