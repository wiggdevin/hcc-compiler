"""SC10: Verify _fake_call_llm in test_patterns_smoke raises on unmatched prompt.

Two tests:
1. A prompt that matches an existing branch returns the expected canned JSON.
2. A prompt that matches NO branch causes pytest.fail() to fire.

We import the helper via importlib to avoid package-relative import issues
(tests/ has an __init__.py, so 'import test_patterns_smoke' doesn't work directly).
"""
from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

# Load test_patterns_smoke as a module without treating it as a package member.
_smoke_path = Path(__file__).parent / "test_patterns_smoke.py"
_spec = importlib.util.spec_from_file_location("_smoke_mod", _smoke_path)
_smoke_mod = importlib.util.module_from_spec(_spec)
sys.modules.setdefault("_smoke_mod", _smoke_mod)
_spec.loader.exec_module(_smoke_mod)

_fake_call_llm = _smoke_mod._fake_call_llm
_DOMAIN_PREFIX = _smoke_mod._DOMAIN_PREFIX

from hcc_compiler.llm.anthropic_client import LLMRequest


def _make_req(prompt: str) -> LLMRequest:
    return LLMRequest(
        system="irrelevant",
        user_prompt=prompt,
        model="claude-sonnet-4-6",
        max_tokens=256,
        temperature=0.0,
    )


def test_matched_prompt_returns_canned_json():
    """A prompt containing 'domain=nutrition' returns the nutrition canned pattern."""
    req = _make_req("ATOMS:\n- id=EA-NUT-001 domain=nutrition claim='test' effect='test'")
    result = _fake_call_llm(req)
    data = json.loads(result)
    assert data["domain"] == "nutrition"
    assert data["id"].startswith(f"RP-{_DOMAIN_PREFIX['nutrition']}-")


def test_unmatched_prompt_raises():
    """A prompt that matches no branch must hard-fail (AssertionError fires)."""
    req = _make_req("ATOMS:\n- id=EA-UNK-001 domain=unknown claim='test' effect='test'")
    # raise AssertionError(...) — subclasses Exception (not BaseException), so a
    # broad `except Exception` in any future production caller will still see it.
    with pytest.raises(AssertionError, match="no canned response for prompt"):
        _fake_call_llm(req)
