from __future__ import annotations
import json
import os
from dataclasses import dataclass
from urllib.request import Request, urlopen


@dataclass
class GLMRequest:
    model: str
    system: str
    user_prompt: str
    max_tokens: int = 1024
    temperature: float = 0.2


def call_llm(req: GLMRequest, timeout: float = 90.0) -> str:
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN")
    if not token:
        raise RuntimeError("ANTHROPIC_AUTH_TOKEN not set — refusing live LLM call")
    base = os.environ.get("ANTHROPIC_BASE_URL", "https://api.z.ai/api/anthropic").rstrip("/")
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
