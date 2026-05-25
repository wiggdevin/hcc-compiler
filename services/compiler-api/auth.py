"""Supabase JWT verification for the compiler API.

Tokens are HS256-signed by Supabase using the project's JWT secret.
The `sub` claim is the coach UUID (Supabase user id).
"""
from __future__ import annotations

import os

import jwt
from fastapi import Header, HTTPException


def _jwt_secret() -> str:
    secret = os.environ.get("SUPABASE_JWT_SECRET", "")
    if not secret:
        raise RuntimeError("SUPABASE_JWT_SECRET is not set")
    return secret


async def get_current_coach(authorization: str = Header(...)) -> str:
    """Return coach UUID from a validated Supabase JWT.

    Raises HTTPException(401) if the header is missing, malformed, expired,
    or the signature does not verify.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization header must use Bearer scheme")

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=401, detail="Bearer token is empty")

    try:
        secret = _jwt_secret()
        payload = jwt.decode(
            token,
            secret,
            algorithms=["HS256"],
            options={"verify_aud": False},  # Supabase tokens have audience=authenticated
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError as exc:
        raise HTTPException(status_code=401, detail=f"Invalid token: {exc}")

    sub = payload.get("sub")
    if not sub:
        raise HTTPException(status_code=401, detail="Token missing sub claim")

    return str(sub)
