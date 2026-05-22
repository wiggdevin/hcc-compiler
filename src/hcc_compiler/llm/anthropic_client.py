from __future__ import annotations
# Renamed from glm_client.py (2026-05-22). Z.AI / GLM banned per Plan 3 directive.
import json
import os
from dataclasses import dataclass, field
from urllib.request import Request, urlopen

_DEFAULT_MODEL_ANTHROPIC = "claude-sonnet-4-6"
_DEFAULT_MODEL_OPENAI = "gpt-5.5"


def _default_model() -> str:
    if os.environ.get("HCC_SYNTH_PROVIDER", "").lower() == "openai":
        return _DEFAULT_MODEL_OPENAI
    return _DEFAULT_MODEL_ANTHROPIC


@dataclass
class LLMRequest:
    system: str
    user_prompt: str
    model: str = field(default_factory=_default_model)
    max_tokens: int = 1024
    temperature: float = 0.2


# Backward-compat alias — remove once all callers migrated
GLMRequest = LLMRequest


def call_llm(req: LLMRequest, timeout: float = 90.0) -> str:
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN")
    if not token:
        raise RuntimeError("ANTHROPIC_AUTH_TOKEN not set — refusing live LLM call")
    base = os.environ.get("ANTHROPIC_BASE_URL", "http://localhost:11455").rstrip("/")
    url = f"{base}/v1/messages"
    body = {
        "model": req.model,
        "max_tokens": req.max_tokens,
        "temperature": req.temperature,
        "system": req.system,
        "messages": [{"role": "user", "content": req.user_prompt}],
    }
    payload = json.dumps(body).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01",
        "X-api-key": token,
        "Authorization": f"Bearer {token}",
    }
    request = Request(url, data=payload, headers=headers, method="POST")
    with urlopen(request, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    parts = [b.get("text", "") for b in data.get("content", []) if b.get("type") == "text"]
    return "".join(parts).strip()
