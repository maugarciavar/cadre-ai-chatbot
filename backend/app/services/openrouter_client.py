from functools import lru_cache

from openai import OpenAI, OpenAIError

from app.config import settings
from app.knowledge.system_prompt import build_system_prompt
from app.models import ChatMessage, ChatResult


class OpenRouterServiceError(Exception):
    """Raised when the OpenRouter API call fails, times out, or returns an
    unparseable response. routers/chat.py catches this and translates it
    into an HTTP error -- it never touches the OpenAI SDK directly."""


@lru_cache(maxsize=1)
def _get_client() -> OpenAI:
    # OpenRouter exposes an OpenAI-compatible Chat Completions API, so the
    # official OpenAI SDK works unmodified -- only the base_url and key differ.
    return OpenAI(
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        timeout=settings.openrouter_timeout_seconds,
        max_retries=2,
    )


def get_chat_result(history: list[ChatMessage], message: str) -> ChatResult:
    """Send the conversation to OpenRouter and return a structured ChatResult.

    This is the only function in the codebase that calls the OpenAI SDK.
    The model, system prompt, and response schema are all assembled here.
    """
    client = _get_client()
    messages = [{"role": "system", "content": build_system_prompt()}]
    messages.extend({"role": m.role, "content": m.content} for m in history)
    messages.append({"role": "user", "content": message})

    try:
        response = client.chat.completions.parse(
            model=settings.openrouter_model,
            messages=messages,
            response_format=ChatResult,
        )
    except OpenAIError as exc:
        # Catches every SDK-raised error: timeouts, connection failures, rate
        # limits, API errors, and the structured-output-specific
        # LengthFinishReasonError / ContentFilterFinishReasonError (which
        # subclass OpenAIError directly, not APIError).
        raise OpenRouterServiceError(f"OpenRouter request failed: {exc}") from exc

    parsed = response.choices[0].message.parsed
    if parsed is None:
        raise OpenRouterServiceError("OpenRouter response could not be parsed into ChatResult")
    return parsed
