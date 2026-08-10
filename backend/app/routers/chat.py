from fastapi import APIRouter, HTTPException

from app.config import settings
from app.models import ChatRequest, ChatResult
from app.services.openrouter_client import OpenRouterServiceError, get_chat_result

router = APIRouter()


@router.post("/api/chat", response_model=ChatResult)
def chat(request: ChatRequest) -> ChatResult:
    if len(request.message) > settings.max_message_length:
        raise HTTPException(
            status_code=422,
            detail=f"Message exceeds the {settings.max_message_length} character limit.",
        )

    # Keep only the most recent turns -- a simple cap, not token counting.
    history = request.history[-settings.max_history_messages :]

    try:
        return get_chat_result(history=history, message=request.message)
    except OpenRouterServiceError as exc:
        raise HTTPException(
            status_code=503,
            detail="Cadre AI chatbot is temporarily unavailable. Please try again shortly.",
        ) from exc
