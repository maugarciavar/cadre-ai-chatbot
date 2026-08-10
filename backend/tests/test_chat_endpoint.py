import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.main import app
from app.models import ChatResult
from app.routers import chat as chat_router
from app.services.openrouter_client import OpenRouterServiceError

client = TestClient(app)


def test_chat_returns_normal_reply(monkeypatch):
    monkeypatch.setattr(
        chat_router,
        "get_chat_result",
        lambda history, message: ChatResult(reply="Cadre AI helps with AI strategy.", escalate=False),
    )

    response = client.post("/api/chat", json={"message": "What does Cadre AI do?", "history": []})

    assert response.status_code == 200
    assert response.json() == {"reply": "Cadre AI helps with AI strategy.", "escalate": False}


def test_chat_returns_escalation(monkeypatch):
    monkeypatch.setattr(
        chat_router,
        "get_chat_result",
        lambda history, message: ChatResult(reply="I don't have that -- please contact us.", escalate=True),
    )

    response = client.post("/api/chat", json={"message": "What's your refund policy?", "history": []})

    assert response.status_code == 200
    assert response.json()["escalate"] is True


def test_chat_rejects_oversized_message(monkeypatch):
    called = False

    def fake_get_chat_result(history, message):
        nonlocal called
        called = True
        return ChatResult(reply="unused", escalate=False)

    monkeypatch.setattr(chat_router, "get_chat_result", fake_get_chat_result)

    too_long = "a" * (settings.max_message_length + 1)
    response = client.post("/api/chat", json={"message": too_long, "history": []})

    assert response.status_code == 422
    assert called is False  # never reached the OpenRouter service


def test_chat_truncates_history_to_configured_limit(monkeypatch):
    captured = {}

    def fake_get_chat_result(history, message):
        captured["history"] = history
        return ChatResult(reply="ok", escalate=False)

    monkeypatch.setattr(chat_router, "get_chat_result", fake_get_chat_result)
    monkeypatch.setattr(settings, "max_history_messages", 3)

    long_history = [
        {"role": "user", "content": f"message {i}"} for i in range(10)
    ]
    response = client.post("/api/chat", json={"message": "latest", "history": long_history})

    assert response.status_code == 200
    assert len(captured["history"]) == 3
    # Truncation keeps the most recent turns, not the oldest.
    assert captured["history"][-1].content == "message 9"


def test_chat_returns_503_on_service_error(monkeypatch):
    def raise_error(history, message):
        raise OpenRouterServiceError("boom")

    monkeypatch.setattr(chat_router, "get_chat_result", raise_error)

    response = client.post("/api/chat", json={"message": "hello", "history": []})

    assert response.status_code == 503
