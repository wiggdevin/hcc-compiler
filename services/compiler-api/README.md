# compiler-api — operating runbook

FastAPI sidecar that wraps `hcc_compiler.sp2.compile.compile()` behind an HTTP API.
Deployed to Fly.io at `https://hcc-compiler-api.fly.dev`.

---

## Authentication

`/compile` is protected by a **static bearer token** shared between the Vercel edge
(`web/app/api/intakes/[id]/compile/route.ts`) and this service. The web layer
authenticates the coach via Supabase first, then forwards the request with the
shared `COMPILER_API_TOKEN`. This service trusts that boundary and only checks
that the bearer matches.

There is **no JWT verification** here, despite earlier versions of this doc. The
auth is intentionally simple because the public surface is the web edge, not
this service.

---

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `COMPILER_API_TOKEN` | **Yes** | — | Shared bearer token. Service exits at startup if missing. The web edge sends this in `Authorization: Bearer <token>`. |
| `LIBRARY_DB_PATH` | No | `/data/library.db` | Path to the SQLite library index. `entrypoint.sh` seeds it from `/data-seed/library.db` (baked into the image) on first boot or whenever the seed is newer. |
| `HCC_LIBRARY_ROOT` | No | `/app/library` | Path to the `library/` directory (atoms + patterns source files). Unused at request time; reserved for admin rebuild jobs. |
| `MAX_BODY_BYTES` | No | `262144` (256 KiB) | Hard cap on request body size. Larger POSTs get 413. ClientIntake payloads are typically <5 KiB. |
| `PORT` | No | `8080` | TCP port uvicorn binds to. Fly convention is 8080. |
| `LOG_LEVEL` | No | `INFO` | Python logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

The service **fails at startup** if `COMPILER_API_TOKEN` is missing.

---

## Rate limiting

Per-IP, via `slowapi`:

- **All routes**: 60 requests / minute (default).
- **`POST /compile`**: 30 requests / minute (tighter — each compile burns ~1–5 s of CPU + SQL queries).

Over-limit requests get `429 {"error": "rate_limited", ...}`.

---

## API surface

```
GET  /healthz            unauthenticated  {"ok": true, "library_version": "..."}
GET  /library/version    unauthenticated  {"library_version": "...", "pattern_count": N, "atom_count": M}
POST /compile            Bearer token     {"json": <EvidencePack>, "md": "<markdown string>"}
```

### POST /compile

**Headers:** `Authorization: Bearer <COMPILER_API_TOKEN>`

**Body (JSON):**
```json
{
  "intake": { ...ClientIntake fields... },
  "top_k": 30,
  "applicability_threshold": 0.5
}
```

Or pass a raw YAML string instead of a pre-parsed object:
```json
{
  "intake_yaml": "client_id: ...\nlibrary_version: ...\n...",
  "top_k": 30,
  "applicability_threshold": 0.5
}
```

**Response 200:**
```json
{
  "json": { ...EvidencePack... },
  "md": "# Personalized Evidence Pack — ..."
}
```

**Error responses:**
- `401` — missing/malformed/wrong bearer token
- `409` — `LibraryVersionMismatch` (intake.library_version != DB version)
- `413` — body exceeds `MAX_BODY_BYTES`
- `422` — pydantic validation failure on intake fields, or unparseable `intake_yaml`
- `429` — per-IP rate limit hit
- `500` — unexpected compile error (body contains `{"error": "compile_failed", "message": "..."}`)

---

## Per-request logs

Every request emits a single INFO line via stdlib logging:

```
2026-05-28 13:41:18,234 INFO compiler-api req method=POST path=/compile status=200 latency_ms=4732
```

POST /compile additionally emits a leading line with `top_k` and `applicability_threshold`. Errors emit a `logger.exception` traceback ahead of the request line.

The format is `%(asctime)s %(levelname)s %(name)s %(message)s` — plain text with a
JSON-ish KV tail. If you want full JSON logs, swap `logging.Formatter` in `main.py`
to a structured one (e.g. `python-json-logger`) — no code re-architecture needed.

---

## Deploy steps

### Prerequisites

```bash
brew install flyctl
fly auth login
```

### First-time launch

Run from the **repo root** so the build context includes `src/`, `library/`, `pyproject.toml`:

```bash
fly launch \
  --name hcc-compiler-api \
  --region iad \
  --no-deploy \
  --config services/compiler-api/fly.toml
```

When prompted, say **no** to adding a Postgres database (we use Supabase).

### Create persistent volume

```bash
fly volume create library_data --app hcc-compiler-api --region iad --size 1
```

The volume holds `/data/library.db`. The image bakes a seed at `/data-seed/library.db`;
`entrypoint.sh` copies seed → `/data/` if the seed is newer (or if `/data/library.db`
doesn't exist yet). This means a normal `fly deploy` propagates library changes without
manual `fly ssh sftp` surgery.

### Set secrets

```bash
fly secrets set --app hcc-compiler-api \
  COMPILER_API_TOKEN="$(zsvault get compiler-api-token)"
```

The same value must be set on Vercel (`COMPILER_API_TOKEN` in the web project's
production env).

### Deploy

```bash
# Build library.db locally first so it gets baked into the image as the seed.
uv run python scripts/curation/build_index.py library library.db

fly deploy \
  --app hcc-compiler-api \
  --config services/compiler-api/fly.toml \
  --dockerfile services/compiler-api/Dockerfile \
  --build-context . \
  --strategy immediate
```

Verify:
```bash
curl https://hcc-compiler-api.fly.dev/library/version
# {"library_version":"0.2.0","pattern_count":22,"atom_count":215}
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `RuntimeError: Missing required env vars: COMPILER_API_TOKEN` on startup | Secret not set | `fly secrets set COMPILER_API_TOKEN=...` |
| `401 Invalid bearer token` | Vercel and Fly have different `COMPILER_API_TOKEN` values | Sync the value: pull from `zsvault get compiler-api-token`; set on both. |
| `409 LibraryVersionMismatch` | Intake YAML has old `library_version` field | Update `library_version` in intake; or update the form default in `web/lib/intake-yaml.ts` |
| `413 payload_too_large` | Intake body > 256 KiB | Trim the intake (probably an oversized `current_regimen` free-text). Raise `MAX_BODY_BYTES` env var if legit. |
| `429 rate_limited` | Per-IP rate limit on `/compile` (30/min) hit | Back off; if legitimate concurrent traffic, raise the limit in `main.py:compile_endpoint`. |
| `500 compile_failed: unable to open database file` | `/data/library.db` missing on volume AND `/data-seed/library.db` missing from image | `fly ssh console` and inspect `/data-seed/`. Redeploy with library.db committed to repo root, OR `fly ssh sftp` `put library.db /data/library.db`. |
| Cold start > 30s | Fly scaled to 0 machines + fastembed loading nomic-embed-text weights | Expected on first request. Upgrade to `min_machines_running = 1` for production latency. |
| High memory usage | Large library.db with many embeddings | Upgrade VM to `memory = "1gb"` in `fly.toml`. |

---

## Local dev

```bash
cd /path/to/hcc-compiler
pip install -e .
pip install -r services/compiler-api/requirements.txt

cd services/compiler-api
COMPILER_API_TOKEN=dev-secret \
LIBRARY_DB_PATH=../../library.db \
uvicorn main:app --reload --port 8080
```

Smoke + integration tests:
```bash
pytest tests/ -q
```
