# Aura Clinic — hcc-compiler frontend

Read-only client-plan navigator. Next.js 16 + Tailwind v4 + Framer Motion + Lucide.

## Run

```bash
cd web
pnpm install     # only once
pnpm dev         # http://localhost:3000
```

Loads compiled plans from `../docs/examples/sp2/*.json` and intakes from `../tests/fixtures/intakes/*.yaml` via Server Components at request time. No env vars, no API calls.

## Routes

| Path | Surface |
|---|---|
| `/clients/<id>/intake` | Captured intake — anthropometrics, regimen, constraints |
| `/clients/<id>/overview` | Plan confidence score ring · safety preflight · 6 domain tiles |
| `/clients/<id>/diet` | Nutrition patterns + atoms |
| `/clients/<id>/workout` | Training + conditioning |
| `/clients/<id>/recovery` | Recovery + supplements + behavioral |
| `/clients/<id>/literature` | Deduped citation index with existence + faithfulness verdicts |

`<id>` is one of: `amy`, `carl`, `sam`, `bradley`, `david`, `jackson`, `sarah`, `sebastian`, `tori` (see `lib/data/personas.ts`).

## Architecture

- **`lib/data/types.ts`** — TS mirror of `EvidencePack` (`src/hcc_compiler/sp2/pack.py`)
- **`lib/data/loader.ts`** — `loadEvidencePack`, `loadIntake` (cached per request)
- **`lib/scoring.ts`** — confidence + citation-integrity formulas
- **`components/glass-card.tsx`** — gradient-border shell, used everywhere

If `pack.py` schema drifts, hand-update `types.ts` to match.
