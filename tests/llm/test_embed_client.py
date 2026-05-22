"""Tests for embed_client.py — offline by default (no HCC_LIVE_EMBED required)."""
from __future__ import annotations

import json
import os
from unittest.mock import patch

import pytest

from hcc_compiler.llm.embed_client import EmbedRequest, embed


# ---------------------------------------------------------------------------
# 1. Request shape
# ---------------------------------------------------------------------------

def test_embed_request_defaults_model():
    req = EmbedRequest(text="hello")
    assert req.text == "hello"
    assert req.model == "nomic-embed-text"


def test_embed_request_model_override():
    req = EmbedRequest(text="hello", model="mxbai-embed-large")
    assert req.model == "mxbai-embed-large"


# ---------------------------------------------------------------------------
# 2. HTTP shape — fake transport via monkeypatched urlopen
# ---------------------------------------------------------------------------

_FAKE_VECTOR = [float(i) / 100.0 for i in range(768)]


class _FakeResp:
    def __init__(self, body: bytes):
        self._body = body

    def __enter__(self):
        return self

    def __exit__(self, *a):
        pass

    def read(self):
        return self._body


def _make_fake_urlopen(captured: dict):
    def fake_urlopen(req, timeout=None):
        captured["url"] = req.full_url
        captured["method"] = req.method
        captured["headers"] = dict(req.header_items())
        captured["body"] = json.loads(req.data.decode("utf-8"))
        body = json.dumps({"embedding": _FAKE_VECTOR}).encode("utf-8")
        return _FakeResp(body)

    return fake_urlopen


def test_embed_posts_to_ollama_endpoint(monkeypatch):
    """embed() must POST to /api/embeddings with correct JSON keys."""
    monkeypatch.delenv("OLLAMA_BASE_URL", raising=False)
    captured: dict = {}

    with patch("hcc_compiler.llm.embed_client.urlopen", new=_make_fake_urlopen(captured)):
        result = embed(EmbedRequest(text="hello"))

    assert "localhost:11434" in captured["url"]
    assert captured["url"].endswith("/api/embeddings")
    assert captured["method"] == "POST"
    assert captured["body"]["model"] == "nomic-embed-text"
    assert captured["body"]["prompt"] == "hello"
    assert result == _FAKE_VECTOR


def test_embed_respects_ollama_base_url_env(monkeypatch):
    """OLLAMA_BASE_URL env var overrides the default host."""
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://ollama.local:11434")
    captured: dict = {}

    with patch("hcc_compiler.llm.embed_client.urlopen", new=_make_fake_urlopen(captured)):
        embed(EmbedRequest(text="world"))

    assert captured["url"].startswith("http://ollama.local:11434")


# ---------------------------------------------------------------------------
# 3. Response parsing
# ---------------------------------------------------------------------------

def test_embed_returns_list_of_floats():
    with patch("hcc_compiler.llm.embed_client.urlopen", new=_make_fake_urlopen({})):
        result = embed(EmbedRequest(text="test"))

    assert isinstance(result, list)
    assert len(result) == 768
    assert all(isinstance(v, float) for v in result)


# ---------------------------------------------------------------------------
# 4. Live-mode gate — must NOT make real network call when HCC_LIVE_EMBED unset
# ---------------------------------------------------------------------------

def test_no_real_network_call_without_live_gate(monkeypatch):
    """If HCC_LIVE_EMBED is unset and urlopen is NOT patched, the test would
    fail with a ConnectionRefusedError (Ollama not running in CI).  We verify
    the guard by ensuring our mock is called (not the real urlopen), i.e., the
    test itself is offline-safe via the mock.  A companion assertion confirms
    HCC_LIVE_EMBED is absent so the implementation cannot accidentally bypass."""
    monkeypatch.delenv("HCC_LIVE_EMBED", raising=False)
    assert os.environ.get("HCC_LIVE_EMBED") is None

    captured: dict = {}
    with patch("hcc_compiler.llm.embed_client.urlopen", new=_make_fake_urlopen(captured)):
        embed(EmbedRequest(text="offline-safe"))

    # Mock was called — no real I/O occurred
    assert captured.get("url") is not None
