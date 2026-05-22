import json
from unittest.mock import patch
from hcc_compiler.llm.glm_client import call_llm, GLMRequest


def test_call_llm_posts_anthropic_messages_payload(monkeypatch):
    monkeypatch.setenv("ANTHROPIC_AUTH_TOKEN", "test-token")
    monkeypatch.setenv("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic")
    captured = {}

    class _Resp:
        def __enter__(self): return self
        def __exit__(self, *a): pass
        def read(self_inner):
            return json.dumps({
                "id": "msg_1",
                "content": [{"type": "text", "text": "ok"}],
                "model": "glm-4.6",
            }).encode("utf-8")

    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["headers"] = dict(req.header_items())
        captured["body"] = json.loads(req.data.decode("utf-8"))
        return _Resp()

    with patch("hcc_compiler.llm.glm_client.urlopen", new=fake_urlopen):
        out = call_llm(GLMRequest(
            model="glm-4.6",
            system="you are helpful",
            user_prompt="say ok",
            max_tokens=64,
        ))

    assert captured["url"].rstrip("/").endswith("/v1/messages")
    assert captured["headers"].get("X-api-key") == "test-token" \
        or captured["headers"].get("Authorization") == "Bearer test-token"
    assert captured["body"]["model"] == "glm-4.6"
    assert captured["body"]["max_tokens"] == 64
    assert captured["body"]["messages"][0]["role"] == "user"
    assert out == "ok"


def test_call_llm_raises_without_token(monkeypatch):
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    import pytest
    with pytest.raises(RuntimeError):
        call_llm(GLMRequest(model="glm-4.6", system="", user_prompt="x", max_tokens=1))
