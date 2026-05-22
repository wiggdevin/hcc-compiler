"""Tests for embed_client retry / backoff behaviour.

Three scenarios:
  1. Transient ConnectionError on first 2 attempts → succeeds on 3rd.
  2. ConnectionError on all 3 attempts → raises after exhausting budget.
  3. 4xx HTTP response → raises immediately, no retry.
"""
from __future__ import annotations

import json
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

import pytest

from hcc_compiler.llm.embed_client import EmbedRequest, embed

_FAKE_VECTOR = [0.1, 0.2, 0.3]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _fake_response(vector: list[float]):
    """Return a context-manager mock whose .read() yields a valid embedding JSON."""
    body = json.dumps({"embedding": vector}).encode("utf-8")
    resp = MagicMock()
    resp.__enter__ = lambda s: s
    resp.__exit__ = MagicMock(return_value=False)
    resp.read.return_value = body
    return resp


def _http_error(code: int) -> HTTPError:
    return HTTPError(url="http://localhost:11434/api/embeddings", code=code,
                     msg="error", hdrs=None, fp=None)


# ---------------------------------------------------------------------------
# Test 1 — retry recovers on 3rd attempt
# ---------------------------------------------------------------------------

def test_retry_recovers_on_third_attempt(monkeypatch):
    """ConnectionError on attempts 1 & 2; success on attempt 3."""
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)

    call_count = 0

    def fake_urlopen(req, timeout=None):
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise ConnectionError("connection refused")
        return _fake_response(_FAKE_VECTOR)

    with patch("hcc_compiler.llm.embed_client.urlopen", new=fake_urlopen), \
         patch("hcc_compiler.llm.embed_client.time.sleep"):  # skip real sleeps
        result = embed(EmbedRequest(text="hello"))

    assert result == _FAKE_VECTOR
    assert call_count == 3


# ---------------------------------------------------------------------------
# Test 2 — budget exhausted → raises
# ---------------------------------------------------------------------------

def test_raises_after_exhausting_retry_budget(monkeypatch):
    """ConnectionError on every attempt → embed() must raise after 3 tries."""
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)

    call_count = 0

    def fake_urlopen(req, timeout=None):
        nonlocal call_count
        call_count += 1
        raise ConnectionError("connection refused")

    with patch("hcc_compiler.llm.embed_client.urlopen", new=fake_urlopen), \
         patch("hcc_compiler.llm.embed_client.time.sleep"):
        with pytest.raises(ConnectionError):
            embed(EmbedRequest(text="hello"))

    assert call_count == 3  # tried exactly 3 times


# ---------------------------------------------------------------------------
# Test 3 — 4xx is permanent → raises immediately, no retry
# ---------------------------------------------------------------------------

def test_4xx_raises_immediately_without_retry(monkeypatch):
    """A 404 (or any 4xx) must propagate immediately — no retry."""
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)

    call_count = 0

    def fake_urlopen(req, timeout=None):
        nonlocal call_count
        call_count += 1
        raise _http_error(404)

    with patch("hcc_compiler.llm.embed_client.urlopen", new=fake_urlopen), \
         patch("hcc_compiler.llm.embed_client.time.sleep"):
        with pytest.raises(HTTPError) as exc_info:
            embed(EmbedRequest(text="hello"))

    assert exc_info.value.code == 404
    assert call_count == 1  # no retry on 4xx
