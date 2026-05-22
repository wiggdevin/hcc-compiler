from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from urllib.request import Request, urlopen

_DEFAULT_MODEL = "nomic-embed-text"
_DEFAULT_TIMEOUT = 15.0


@dataclass
class EmbedRequest:
    text: str
    model: str = field(default=_DEFAULT_MODEL)


def embed(req: EmbedRequest, timeout: float = _DEFAULT_TIMEOUT) -> list[float]:
    base = os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434").rstrip("/")
    url = f"{base}/api/embeddings"
    body = {"model": req.model, "prompt": req.text}
    payload = json.dumps(body).encode("utf-8")
    headers = {"Content-Type": "application/json"}
    request = Request(url, data=payload, headers=headers, method="POST")
    with urlopen(request, timeout=timeout) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["embedding"]
