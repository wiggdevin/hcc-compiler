"""FastAPI compiler sidecar for hcc-compiler.

Endpoints
---------
GET  /healthz              unauthenticated — liveness probe
GET  /library/version      unauthenticated — library stats
POST /compile              authenticated (Supabase JWT) — run compile()
"""
from __future__ import annotations

import logging
import os
import sqlite3
from pathlib import Path
from typing import Any

import yaml
from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError

from auth import get_current_coach
from compile_runner import run_compile
from hcc_compiler.sp2.compile import LibraryVersionMismatch

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=getattr(logging, log_level, logging.INFO),
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger("compiler-api")

# ---------------------------------------------------------------------------
# Startup validation
# ---------------------------------------------------------------------------
_REQUIRED_ENV = ["SUPABASE_JWT_SECRET"]


def _validate_env() -> None:
    missing = [k for k in _REQUIRED_ENV if not os.environ.get(k)]
    if missing:
        raise RuntimeError(f"Missing required env vars: {', '.join(missing)}")


_validate_env()

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------
app = FastAPI(title="hcc-compiler API", version="0.1.0")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
_LIBRARY_VERSION = "0.1.0"


def _db_path() -> Path:
    return Path(os.environ.get("LIBRARY_DB_PATH", "/data/library.db"))


def _library_stats() -> dict:
    db = _db_path()
    if not db.exists():
        return {"library_version": _LIBRARY_VERSION, "pattern_count": 0, "atom_count": 0}
    try:
        con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        con.row_factory = sqlite3.Row
        row = con.execute("SELECT value FROM meta WHERE key='library_version'").fetchone()
        version = row["value"] if row else _LIBRARY_VERSION
        pattern_count = con.execute("SELECT COUNT(*) FROM patterns").fetchone()[0]
        atom_count = con.execute("SELECT COUNT(*) FROM atoms").fetchone()[0]
        con.close()
        return {"library_version": version, "pattern_count": pattern_count, "atom_count": atom_count}
    except Exception as exc:
        logger.warning("Could not read library stats: %s", exc)
        return {"library_version": _LIBRARY_VERSION, "pattern_count": 0, "atom_count": 0}


# ---------------------------------------------------------------------------
# Request / response models
# ---------------------------------------------------------------------------
class CompileRequest(BaseModel):
    intake: dict | None = None
    intake_yaml: str | None = None
    top_k: int = 30
    applicability_threshold: float = 0.5


class CompileResponse(BaseModel):
    model_config = {"populate_by_name": True}
    json: Any  # field name matches API contract; pydantic v2 allows it
    md: str


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------
@app.get("/healthz")
async def healthz() -> dict:
    stats = _library_stats()
    return {"ok": True, "library_version": stats["library_version"]}


@app.get("/library/version")
async def library_version() -> dict:
    return _library_stats()


@app.post("/compile", response_model=CompileResponse)
async def compile_endpoint(
    body: CompileRequest,
    coach_id: str = Depends(get_current_coach),
) -> CompileResponse:
    logger.info("POST /compile coach=%s top_k=%d threshold=%.2f", coach_id, body.top_k, body.applicability_threshold)

    # Resolve intake dict from either JSON or YAML field.
    if body.intake is not None:
        intake_dict = body.intake
    elif body.intake_yaml is not None:
        try:
            intake_dict = yaml.safe_load(body.intake_yaml)
        except yaml.YAMLError as exc:
            raise HTTPException(status_code=422, detail=f"Invalid YAML: {exc}")
    else:
        raise HTTPException(status_code=422, detail="Provide 'intake' (JSON) or 'intake_yaml' (YAML string)")

    try:
        result = run_compile(
            intake_dict,
            top_k=body.top_k,
            threshold=body.applicability_threshold,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=422, detail=exc.errors())
    except LibraryVersionMismatch as exc:
        raise HTTPException(status_code=409, detail=str(exc))
    except Exception as exc:
        logger.exception("Compile error for coach=%s", coach_id)
        raise HTTPException(status_code=500, detail={"error": "compile_failed", "message": str(exc)})

    return CompileResponse(json=result["json"], md=result["md"])


# ---------------------------------------------------------------------------
# Global error handler — ensure all 500s are structured JSON
# ---------------------------------------------------------------------------
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("Unhandled exception on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"error": "internal_server_error", "message": str(exc)},
    )
