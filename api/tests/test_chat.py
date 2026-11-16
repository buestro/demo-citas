import logging
from types import SimpleNamespace

import pytest

from app import assistant, config


class FakeClient:
    """Stands in for anthropic.Anthropic: records the request, returns a canned response."""

    def __init__(self, blocks=None, stop_reason="end_turn"):
        self.calls = []
        self.blocks = blocks if blocks is not None else [SimpleNamespace(type="text", text="El horario es de lunes a viernes.")]
        self.stop_reason = stop_reason
        self.messages = SimpleNamespace(create=self._create)

    def _create(self, **kwargs):
        self.calls.append(kwargs)
        return SimpleNamespace(content=self.blocks, stop_reason=self.stop_reason)


@pytest.fixture()
def fake(monkeypatch):
    f = FakeClient()
    monkeypatch.setattr(assistant, "get_client", lambda: f)
    return f


def ask(client, *texts, history=None):
    msgs = history or []
    for t in texts:
        msgs.append({"role": "user", "content": t})
    return client.post("/api/chat", json={"messages": msgs})


def test_system_prompt_is_built_from_the_data_file():
    p = assistant.build_system_prompt()
    for item in config.SITE["faq"]:
        assert item["q"] in p
    assert config.SITE["assistant"]["clinical_refusal"] in p
    assert "Clínica Dental Mezquite" in p


def test_request_uses_haiku_low_effort_and_no_sampling_params(client, fake):
    r = ask(client, "¿Cuál es su horario?")
    assert r.status_code == 200 and "horario" in r.json()["reply"].lower()
    call = fake.calls[0]
    assert call["model"] == "claude-haiku-5-5"
    assert call["output_config"] == {"effort": "low"}
    assert call["max_tokens"] == config.ASSISTANT_MAX_TOKENS
    for banned in ("temperature", "top_p", "top_k", "fallbacks", "thinking"):
        assert banned not in call  # Haiku 5.5 rejects sampling params and has no fallbacks
    assert call["messages"] == [{"role": "user", "content": "¿Cuál es su horario?"}]


def test_thinking_blocks_are_skipped(client, monkeypatch):
    f = FakeClient(blocks=[SimpleNamespace(type="thinking", thinking=""), SimpleNamespace(type="text", text="Hola, ¿en qué te ayudo?")])
    monkeypatch.setattr(assistant, "get_client", lambda: f)
    assert ask(client, "hola").json()["reply"] == "Hola, ¿en qué te ayudo?"


def test_refusal_stop_reason_gets_a_friendly_answer(client, monkeypatch):
    f = FakeClient(blocks=[], stop_reason="refusal")
    monkeypatch.setattr(assistant, "get_client", lambda: f)
    assert ask(client, "hola").json()["reply"] == config.SITE["assistant"]["off_topic_refusal"]


def test_missing_api_key_is_a_friendly_503(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.setattr(assistant, "_client", None)
    r = ask(client, "hola")
    assert r.status_code == 503 and "WhatsApp" in r.json()["detail"]


def test_validation(client, fake):
    assert ask(client, "x" * (config.CHAT_MAX_CHARS + 1)).status_code == 422
    bad_end = [{"role": "user", "content": "hola"}, {"role": "assistant", "content": "hola"}]
    assert client.post("/api/chat", json={"messages": bad_end}).status_code == 422
    assert client.post("/api/chat", json={"messages": []}).status_code == 422
    assert client.post("/api/chat", json={"messages": [{"role": "system", "content": "x"}]}).status_code == 422
    assert client.post("/api/chat", json={"messages": [{"role": "user", "content": "hola"}], "website": "spam"}).status_code == 400
    assert fake.calls == []  # nothing invalid reaches the model


def test_conversation_length_is_capped(client, fake):
    # more user turns than a session allows -> 429, and nothing reaches the model
    too_many = [{"role": "user", "content": f"pregunta {i}"} for i in range(config.CHAT_USER_TURNS_PER_SESSION + 1)]
    assert client.post("/api/chat", json={"messages": too_many}).status_code == 429
    assert fake.calls == []
    # a history window longer than the cap is rejected by validation
    window = [{"role": "user" if i % 2 == 0 else "assistant", "content": "x"} for i in range(config.CHAT_MAX_MESSAGES + 1)]
    assert client.post("/api/chat", json={"messages": window}).status_code == 422
    # at the limit it still works and reports how many turns remain
    ok = [{"role": "user", "content": f"pregunta {i}"} for i in range(config.CHAT_USER_TURNS_PER_SESSION)]
    r = client.post("/api/chat", json={"messages": ok})
    assert r.status_code == 200 and r.json()["remaining"] == 0


def test_per_ip_limit(client, fake, monkeypatch):
    monkeypatch.setattr(config, "CHAT_PER_IP_PER_HOUR", 2)
    assert ask(client, "uno").status_code == 200
    assert ask(client, "dos").status_code == 200
    assert ask(client, "tres").status_code == 429


def test_global_daily_cap(client, fake, monkeypatch):
    monkeypatch.setattr(config, "CHAT_PER_DAY_GLOBAL", 1)
    assert ask(client, "uno").status_code == 200
    r = ask(client, "dos")
    assert r.status_code == 503 and "WhatsApp" in r.json()["detail"]


def test_conversations_are_not_logged(client, fake, caplog):
    caplog.set_level(logging.DEBUG)
    secret = "mi-dato-privado-12345"
    ask(client, f"hola {secret}")
    assert secret not in caplog.text
