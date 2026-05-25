# compiler-api — operating runbook

FastAPI sidecar that wraps `hcc_compiler.sp2.compile.compile()` behind an HTTP API.
Deployed to Fly.io at `https://hcc-compiler-api.fly.dev`.

---

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `SUPABASE_JWT_SECRET` | Yes | — | HS256 secret from Supabase project Settings → API → JWT Secret. Used to verify all `/compile` requests. |
| `LIBRARY_DB_PATH` | No | `/data/library.db` | Path to the SQLite library index. On Fly, the persistent volume is mounted at `/data`. |
| `HCC_LIBRARY_ROOT` | No | `/app/library` | Path to the `library/` directory (atoms + patterns source files). Used by admin rebuild jobs, not customer-time requests. |
| `ANTHROPIC_BASE_URL` | No | — | Override for LLM calls made during admin-time `make extract` library harvest. Not used at request time. |
| `PORT` | No | `8080` | TCP port uvicorn binds to. Fly convention is 8080. |
| `LOG_LEVEL` | No | `INFO` | Python logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`). |

The service **fails at startup** if `SUPABASE_JWT_SECRET` is missing.

---

## API surface

```
GET  /healthz            unauthenticated  {"ok": true, "library_version": "..."}
GET  /library/version    unauthenticated  {"library_version": "...", "pattern_count": N, "atom_count": M}
POST /compile            Bearer JWT       {"json": <EvidencePack>, "md": "<markdown string>"}
```

### POST /compile

**Headers:** `Authorization: Bearer <supabase_jwt>`

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
- `401` — missing/invalid/expired JWT
- `409` — `LibraryVersionMismatch` (intake.library_version != DB version)
- `422` — pydantic validation failure on intake fields (body contains error list)
- `500` — unexpected compile error (body contains `{"error": "compile_failed", "message": "..."}`)

---

## Deploy steps

### Prerequisites

```bash
# Install flyctl if needed
brew install flyctl
fly auth login

# Install deps locally for syntax check (optional)
pip install -r services/compiler-api/requirements.txt
```

### 1. Launch (first time only — no-deploy to configure before first push)

Run from the **repo root** so the build context includes `src/`, `library/`, `pyproject.toml`:

```bash
fly launch \
  --name hcc-compiler-api \
  --region iad \
  --no-deploy \
  --config services/compiler-api/fly.toml
```

When prompted, say **no** to adding a Postgres database (we use Supabase).

### 2. Create persistent volume for library.db

```bash
fly volume create library_data \
  --app hcc-compiler-api \
  --region iad \
  --size 1
```

### 3. Set secrets

```bash
fly secrets set \
  --app hcc-compiler-api \
  SUPABASE_JWT_SECRET="$(zsvault get supabase-hcc-jwt-secret)"
```

Optionally set the LLM proxy for admin-time harvest jobs:
```bash
fly secrets set \
  --app hcc-compiler-api \
  ANTHROPIC_BASE_URL="https://hcc.zerosumsolutions.com"
```

### 4. Deploy

```bash
fly deploy \
  --app hcc-compiler-api \
  --config services/compiler-api/fly.toml \
  --dockerfile services/compiler-api/Dockerfile \
  --build-context .
```

### 5. Seed library.db onto the volume (first deploy)

After the machine starts, copy the local `library.db` to the Fly volume:

```bash
fly ssh sftp shell --app hcc-compiler-api
# Then: put library.db /data/library.db
# Or use fly ssh console and wget/curl from a signed URL
```

Alternatively, re-run `make build-library` inside the container if `HCC_LIBRARY_ROOT` is set correctly.

---

## Subsequent deploys

```bash
fly deploy \
  --app hcc-compiler-api \
  --config services/compiler-api/fly.toml \
  --dockerfile services/compiler-api/Dockerfile \
  --build-context .
```

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `RuntimeError: SUPABASE_JWT_SECRET is not set` on startup | Secret not set | `fly secrets set SUPABASE_JWT_SECRET=...` |
| `401 Token has expired` | Supabase JWT is short-lived (~1 hr) | Re-issue token from Supabase client; check client clock skew |
| `409 LibraryVersionMismatch` | Intake YAML has old `library_version` field | Update `library_version` in intake to match DB; or run with `version_check: false` |
| `500 compile_failed: unable to open database file` | `/data/library.db` missing on volume | SSH in and copy `library.db` to `/data/`; verify volume mount in `fly.toml` |
| Cold start > 30s | Fly scaled to 0 machines | Expected; upgrade to `min_machines_running = 1` at $5/mo extra |
| High memory usage | Large library.db with many embeddings | Upgrade VM to `memory = "1gb"` in `fly.toml` |

---

## Local dev

```bash
cd /path/to/hcc-compiler
pip install -e .
pip install -r services/compiler-api/requirements.txt

cd services/compiler-api
SUPABASE_JWT_SECRET=dev-secret \
LIBRARY_DB_PATH=../../library.db \
uvicorn main:app --reload --port 8080
```

Smoke test:
```bash
pytest tests/test_smoke.py -q
```
