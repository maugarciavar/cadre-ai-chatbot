import httpx
import pytest
from openai import APIConnectionError

from app.models import ChatMessage, ChatResult
from app.services import openrouter_client as oc


class _FakeMessage:
    def __init__(self, parsed):
        self.parsed = parsed


class _FakeChoice:
    def __init__(self, parsed):
        self.message = _FakeMessage(parsed)


class _FakeCompletion:
    def __init__(self, parsed):
        self.choices = [_FakeChoice(parsed)]


class _FakeCompletions:
    def __init__(self, parsed=None, exc=None):
        self._parsed = parsed
        self._exc = exc
        self.last_call_kwargs: dict | None = None

    def parse(self, **kwargs):
        self.last_call_kwargs = kwargs
        if self._exc:
            raise self._exc
        return _FakeCompletion(self._parsed)


class _FakeChat:
    def __init__(self, parsed=None, exc=None):
        self.completions = _FakeCompletions(parsed=parsed, exc=exc)


class _FakeClient:
    def __init__(self, parsed=None, exc=None):
        self.chat = _FakeChat(parsed=parsed, exc=exc)


def test_get_chat_result_returns_parsed_result(monkeypatch):
    expected = ChatResult(reply="Cadre AI helps businesses with AI strategy.", escalate=False)
    fake_client = _FakeClient(parsed=expected)
    monkeypatch.setattr(oc, "_get_client", lambda: fake_client)

    result = oc.get_chat_result(history=[], message="What does Cadre AI do?")

    assert result == expected
    kwargs = fake_client.chat.completions.last_call_kwargs
    assert kwargs["model"]
    assert kwargs["response_format"] is ChatResult
    assert kwargs["messages"][0]["role"] == "system"
    assert "Cadre" in kwargs["messages"][0]["content"]


def test_get_chat_result_sends_history_then_new_message(monkeypatch):
    fake_client = _FakeClient(parsed=ChatResult(reply="ok", escalate=False))
    monkeypatch.setattr(oc, "_get_client", lambda: fake_client)

    history = [
        ChatMessage(role="user", content="hi"),
        ChatMessage(role="assistant", content="hello, how can I help?"),
    ]
    oc.get_chat_result(history=history, message="thanks")

    sent_messages = fake_client.chat.completions.last_call_kwargs["messages"]
    # messages[0] is the system prompt; the rest is history + new message
    assert sent_messages[1:] == [
        {"role": "user", "content": "hi"},
        {"role": "assistant", "content": "hello, how can I help?"},
        {"role": "user", "content": "thanks"},
    ]


def test_get_chat_result_wraps_sdk_errors(monkeypatch):
    fake_request = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    fake_client = _FakeClient(exc=APIConnectionError(request=fake_request))
    monkeypatch.setattr(oc, "_get_client", lambda: fake_client)

    with pytest.raises(oc.OpenRouterServiceError):
        oc.get_chat_result(history=[], message="hello")


def test_get_chat_result_raises_when_response_unparseable(monkeypatch):
    fake_client = _FakeClient(parsed=None)
    monkeypatch.setattr(oc, "_get_client", lambda: fake_client)

    with pytest.raises(oc.OpenRouterServiceError):
        oc.get_chat_result(history=[], message="hello")
