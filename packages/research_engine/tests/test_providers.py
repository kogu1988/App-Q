"""DeepSeek sağlayıcı adaptörü — kwargs iletimi regresyon testi.

Korunan değer: Gerçek DeepSeek API çağrısı. Testler `FakeModel` kullandığı için
`DeepSeekResearchModel` doğrudan test edilmiyordu; tenacity'nin yanlış
kullanılması (`_retry_policy()(fn)(**kwargs)`) TÜM gerçek LLM çağrılarını
sessizce kırmıştı (OpenAI SDK: "Missing required arguments"). Bu test, kwargs'ın
`create()`'e gerçekten geçtiğini doğrular — ağ çağrısı YAPMAZ.
"""
from __future__ import annotations

import pytest


class _FakeCompletions:
    def __init__(self) -> None:
        self.captured: dict = {}

    def create(self, **kwargs):
        self.captured.update(kwargs)
        return "FAKE_RESPONSE"


class _FakeChat:
    def __init__(self, completions: _FakeCompletions) -> None:
        self.completions = completions


class _FakeClient:
    def __init__(self) -> None:
        self.completions = _FakeCompletions()
        self.chat = _FakeChat(self.completions)


@pytest.fixture()
def model(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-key")
    from packages.research_engine.providers import DeepSeekResearchModel

    m = DeepSeekResearchModel(model_id="deepseek-v4-flash")
    fake = _FakeClient()
    m.client = fake  # type: ignore[assignment]
    return m, fake


def test_chat_forwards_model_and_messages(model):
    """`_chat` kwargs'ı `create()`'e olduğu gibi iletmeli (argümansız çağrı OLMAMALI)."""
    m, fake = model
    out = m._chat(model="deepseek-v4-flash", messages=[{"role": "user", "content": "merhaba"}])

    assert out == "FAKE_RESPONSE"
    assert fake.completions.captured["model"] == "deepseek-v4-flash"
    assert fake.completions.captured["messages"] == [{"role": "user", "content": "merhaba"}]


def test_chat_forwards_nested_extra_body(model):
    """extra_body (thinking + user_id) kaybolmamalı."""
    m, fake = model
    m._chat(
        model="deepseek-v4-flash",
        messages=[{"role": "user", "content": "x"}],
        extra_body={"thinking": {"type": "enabled"}, "user_id": "u1"},
    )

    assert fake.completions.captured["extra_body"]["thinking"] == {"type": "enabled"}
    assert fake.completions.captured["extra_body"]["user_id"] == "u1"


def test_chat_forwards_response_format(model):
    m, fake = model
    m._chat(
        model="deepseek-v4-flash",
        messages=[{"role": "user", "content": "x"}],
        response_format={"type": "json_object"},
    )
    assert fake.completions.captured["response_format"] == {"type": "json_object"}


def test_chat_without_client_raises(monkeypatch):
    """Client yoksa açık hata vermeli (sessiz başarısızlık olmamalı)."""
    monkeypatch.setenv("DEEPSEEK_API_KEY", "sk-test-key")
    from packages.research_engine.providers import DeepSeekResearchModel, ModelProviderError

    m = DeepSeekResearchModel(model_id="deepseek-v4-flash")
    m.client = None  # type: ignore[assignment]

    with pytest.raises(ModelProviderError):
        m._chat(model="deepseek-v4-flash", messages=[])
