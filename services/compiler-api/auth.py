"""Bearer-token auth for the compiler API.

The web edge (Vercel `/api/intakes/[id]/compile`) authenticates the coach
via Supabase before forwarding to this service with a shared
`COMPILER_API_TOKEN` bearer. We trust that auth and only verify the static
bearer matches. The coach UUID is read from the request body, not the
token, since the bearer is shared across all coaches.

Rejecting requests without a valid bearer prevents arbitrary public
compile traffic; coach-level authorization is the edge's job.
"""
from __future__ import annotations

import os

from fastapi import Header, HTTPException


def _expected_token() -> str:
    tok = os.environ.get("COMPILER_API_TOKEN", "")
    if not tok:
        raise RuntimeError("COMPILER_API_TOKEN is not set")
    return tok


async def require_bearer(authorization: str | None = Header(default=None)) -> None:
    """Validate the request carries the shared service bearer.

    Raises HTTPException(401) on missing / malformed / mismatched bearer.
    """
    if authorization is None:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=401,
            detail="Authorization header must use Bearer scheme",
        )

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Bearer token is empty")

    if token != _expected_token():
        raise HTTPException(status_code=401, detail="Invalid bearer token")
