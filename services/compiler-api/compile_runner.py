"""Thin wrapper around hcc_compiler.sp2.compile.compile().

Keeps the FastAPI route handler free of compiler-internals knowledge.
"""
from __future__ import annotations

import os
from pathlib import Path

from hcc_compiler.sp2.compile import compile as _compile
from hcc_compiler.sp2.intake import ClientIntake
from hcc_compiler.sp2.render import render_markdown


def _db_path() -> Path:
    return Path(os.environ.get("LIBRARY_DB_PATH", "/data/library.db"))


def run_compile(
    intake_dict: dict,
    top_k: int = 30,
    threshold: float = 0.5,
) -> dict:
    """Return ``{'json': <EvidencePack as dict>, 'md': <rendered markdown>}``.

    Raises ``pydantic.ValidationError`` for bad intake data and lets compiler
    exceptions (e.g. ``LibraryVersionMismatch``) propagate so the route layer
    can map them to appropriate HTTP status codes.
    """
    intake = ClientIntake.model_validate(intake_dict)
    pack = _compile(
        intake,
        db_path=_db_path(),
        top_k=top_k,
        applicability_threshold=threshold,
    )
    md = render_markdown(pack, intake=intake)
    return {
        "json": pack.model_dump(mode="json"),
        "md": md,
    }
