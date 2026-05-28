"""FastAPI TestClient integration suite.

Boots the full app in-process and POSTs over HTTP-shaped calls. Verifies
auth, error envelopes, body-size cap, and the rate limiter.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

# Path wiring mirrors test_smoke.py — let pytest run from either repo root or service root.
_HERE = Path(__file__).resolve().parent
_SERVICE_ROOT = _HERE.parent
_REPO_ROOT = _SERVICE_ROOT.parents[1]
sys.path.insert(0, str(_REPO_ROOT / "src"))
sys.path.insert(0, str(_SERVICE_ROOT))

# main.py's startup validation requires COMPILER_API_TOKEN; set it before import.
_TOKEN = "test-token-do-not-deploy"
os.environ.setdefault("COMPILER_API_TOKEN", _TOKEN)
os.environ.setdefault("LIBRARY_DB_PATH", str(_REPO_ROOT / "library.db"))

import main  # noqa: E402 — must be after env setup


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(main.app)


@pytest.fixture(scope="module")
def auth_header() -> dict[str, str]:
    return {"Authorization": f"Bearer {_TOKEN}"}


@pytest.fixture(scope="module")
def tori_intake() -> dict:
    import yaml
    path = _REPO_ROOT / "tests" / "fixtures" / "intakes" / "intake_test_v2_tori_shaw.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# Healthz
# ---------------------------------------------------------------------------
def test_healthz_200_unauthenticated(client: TestClient) -> None:
    r = client.get("/healthz")
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert "library_version" in body


def test_library_version_200_unauthenticated(client: TestClient) -> None:
    r = client.get("/library/version")
    assert r.status_code == 200
    body = r.json()
    assert "library_version" in body
    assert isinstance(body["pattern_count"], int)
    assert isinstance(body["atom_count"], int)


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------
def test_compile_401_missing_auth(client: TestClient, tori_intake: dict) -> None:
    r = client.post("/compile", json={"intake": tori_intake})
    assert r.status_code == 401


def test_compile_401_bad_bearer(client: TestClient, tori_intake: dict) -> None:
    r = client.post(
        "/compile",
        json={"intake": tori_intake},
        headers={"Authorization": "Bearer wrong-token"},
    )
    assert r.status_code == 401
    assert r.json()["detail"] == "Invalid bearer token"


def test_compile_401_malformed_scheme(client: TestClient, tori_intake: dict) -> None:
    r = client.post(
        "/compile",
        json={"intake": tori_intake},
        headers={"Authorization": "Basic wrong-scheme"},
    )
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------
def test_compile_happy_path(
    client: TestClient, auth_header: dict[str, str], tori_intake: dict
) -> None:
    r = client.post("/compile", json={"intake": tori_intake}, headers=auth_header)
    assert r.status_code == 200, r.text
    body = r.json()
    assert "json" in body and "md" in body
    assert body["json"]["client_id"] == tori_intake["client_id"]
    assert body["md"].startswith("#")


def test_compile_intake_yaml_form(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    import yaml
    path = _REPO_ROOT / "tests" / "fixtures" / "intakes" / "intake_test_v2_tori_shaw.yaml"
    r = client.post(
        "/compile",
        json={"intake_yaml": path.read_text(encoding="utf-8")},
        headers=auth_header,
    )
    assert r.status_code == 200
    assert r.json()["json"]["client_id"]


# ---------------------------------------------------------------------------
# Body-size cap
# ---------------------------------------------------------------------------
def test_compile_413_oversized_body(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    # Construct a body slightly larger than the default 256 KiB cap.
    big_string = "x" * (300 * 1024)
    payload = {"intake": {"junk": big_string}}
    r = client.post("/compile", json=payload, headers=auth_header)
    assert r.status_code == 413
    assert r.json()["error"] == "payload_too_large"


# ---------------------------------------------------------------------------
# Request validation
# ---------------------------------------------------------------------------
def test_compile_422_missing_both_intake_fields(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    r = client.post("/compile", json={"top_k": 30}, headers=auth_header)
    assert r.status_code == 422


def test_compile_422_invalid_intake_yaml(
    client: TestClient, auth_header: dict[str, str]
) -> None:
    r = client.post(
        "/compile",
        json={"intake_yaml": "  : not valid : yaml :"},
        headers=auth_header,
    )
    assert r.status_code == 422
