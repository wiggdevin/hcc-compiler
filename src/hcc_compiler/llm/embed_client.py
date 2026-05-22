from __future__ import annotations

import json
import os
import random
import time
from dataclasses import dataclass, field
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

_DEFAULT_MODEL = "nomic-embed-text"
_DEFAULT_TIMEOUT = 15.0
_MAX_ATTEMPTS = 3
_BACKOFF_BASE = 0.5  # seconds; attempt 2 sleeps ~0.5s, attempt 3 sleeps ~1.0s


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

    last_exc: Exception | None = None
    for attempt in range(_MAX_ATTEMPTS):
        if attempt > 0:
            # Exponential backoff with ±25 % jitter
            sleep_s = _BACKOFF_BASE * (2 ** (attempt - 1)) * (0.75 + random.random() * 0.5)
            time.sleep(sleep_s)
        try:
            request = Request(url, data=payload, headers=headers, method="POST")
            with urlopen(request, timeout=timeout) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data["embedding"]
        except HTTPError as exc:
            # 4xx → permanent failure; re-raise immediately
            if 400 <= exc.code < 500:
                raise
            # 5xx → transient; retry
            last_exc = exc
        except (URLError, TimeoutError, ConnectionError, OSError) as exc:
            # Network-level failures → transient; retry
            last_exc = exc

    assert last_exc is not None
    raise last_exc
