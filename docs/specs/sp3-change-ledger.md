# SP3 — Change Ledger (design)

> **Status:** design only. No implementation in this round. Slice into SP3.1/3.2/3.3 once SaaS launch validates the cost.
> **Author:** Devin (+ Claude)
> **Date:** 2026-05-28
> **Supersedes:** the one-paragraph stub in `docs/specs/sp1-evidence-library-design.md` §8 and the rows in `docs/PRD.md` / `docs/PRD-sp2.md` / `README.md` that name SP3.

---

## §1 Problem

When the evidence library changes — atoms admitted, claims revised, patterns deprecated — every compiled pack downstream is potentially stale. Today, the only staleness signal is a single string compare:

```python
# src/hcc_compiler/sp2/compile.py:55
if intake.library_version != db_version:
    raise LibraryVersionMismatch(...)
```

That fires only when *someone tries to recompile against a different library version*. It never tells us:

1. **Which packs are affected** by a change. (Did the atom that drives Carl's training-volume pattern get revised? Or just an obscure SUP-domain claim that nobody's intake matches?)
2. **What changed** about a given pack. (A locator-quote fix vs a dose-range correction look identical at the library_version level.)
3. **When to nudge the coach**. (Most plans don't need re-sending every time the library bumps; some do.)

For a SaaS with N coaches × M clients each, the naïve answer ("recompile everything on every library bump") is O(N·M) wasted compiles per bump. SP3's job is to make staleness *queryable*, so the coach surface can show "Carl's plan has new evidence available" without us recompiling everything in advance.

---

## §2 Data model

Three node types in the dependency DAG:

- **Atoms** — leaf nodes, content from `library/atoms/<domain>/EA-*.yaml`. Each carries a stable `content_hash`.
- **Patterns** — intermediate nodes, content from `library/patterns/<domain>/RP-*.yaml`. Hash covers the pattern's own fields PLUS the sorted set of backing_atom_ids (so a pattern hash changes if a backing atom is added or removed even if the pattern's prose doesn't change).
- **Packs** — root nodes, the compiled output stored in Supabase Storage. Hash covers `compile_metadata` + the sorted-by-id list of every atom and pattern that surfaced in the output.

Three edge types:

- **atom → pattern** — derived from `pattern.backing_atom_ids`.
- **pattern → pack** — recorded at compile time as the patterns that surfaced per domain.
- **atom → pack** — recorded at compile time for atoms that surfaced standalone (not via a pattern).

**Hash strategy.** sha256 over a canonicalized projection:

1. Load the YAML/JSON.
2. Drop *volatile* fields: `last_reviewed`, `expiry`, `approval` (author name + date), `library_version` (this is the *thing* we're versioning around).
3. Sort dict keys, sort list-of-IDs alphabetically.
4. JSON-dump with `sort_keys=True, ensure_ascii=False`.
5. sha256 the resulting bytes, hex-encode.

The volatile-field drop is critical: a YAML file that only differs by `last_reviewed: 2026-05-28` → `2026-06-15` should produce the same hash. Otherwise every metadata-only review touch triggers a phantom "atom changed" event.

**Storage.** Three new tables in `library.db` (the existing SQLite index — colocated for write-side simplicity):

```sql
CREATE TABLE node_hashes (
  record_id     TEXT PRIMARY KEY,        -- e.g. "EA-NUT-7134" or "RP-NUT-meal-timing-..."
  record_type   TEXT NOT NULL,           -- "atom" | "pattern" | "pack"
  content_hash  TEXT NOT NULL,           -- sha256 hex
  computed_at   TEXT NOT NULL            -- ISO 8601
);

CREATE TABLE pack_provenance (
  pack_id           TEXT NOT NULL,       -- UUID of the pack in Supabase
  source_node_id    TEXT NOT NULL,       -- atom or pattern id
  source_node_type  TEXT NOT NULL,       -- "atom" | "pattern"
  source_hash       TEXT NOT NULL,       -- hash of source node AT COMPILE TIME
  recorded_at       TEXT NOT NULL,
  PRIMARY KEY (pack_id, source_node_id)
);
CREATE INDEX pack_provenance_source_idx
  ON pack_provenance(source_node_id);

CREATE TABLE change_log (
  seq           INTEGER PRIMARY KEY AUTOINCREMENT,
  record_id     TEXT NOT NULL,
  record_type   TEXT NOT NULL,
  old_hash      TEXT,                    -- NULL for first-seen nodes
  new_hash      TEXT NOT NULL,
  detected_at   TEXT NOT NULL
);
CREATE INDEX change_log_record_idx
  ON change_log(record_id, detected_at);
```

---

## §3 Invalidation algorithm

On every `build_index.py` run (after atoms/patterns are loaded but before commit):

1. **Compute fresh hashes.** For each atom and pattern, run the canonical projection + sha256.
2. **Diff against `node_hashes`.** For each record:
   - First-seen → insert into `node_hashes`, write a `change_log` row with `old_hash = NULL`.
   - Unchanged → skip.
   - Changed → update `node_hashes.content_hash`, write a `change_log` row.
3. **Walk to affected packs.** For each row in the change_log that just landed, `SELECT DISTINCT pack_id FROM pack_provenance WHERE source_node_id = ?`. The union across all changed nodes is the set of affected packs.
4. **Emit a JSONL stream** to `library/_change_log.jsonl` (per-run, appended; rotated to `_change_log.YYYY-MM-DD.jsonl` after 30 days):

   ```jsonl
   {"pack_id":"8e316374-…","reason":"atom EA-NUT-7134 changed","detected_at":"2026-05-28T13:41:18Z"}
   {"pack_id":"8e316374-…","reason":"pattern RP-NUT-meal-timing-… changed","detected_at":"2026-05-28T13:41:18Z"}
   ```

   Downstream consumers (the web app, or a future Supabase function) tail this file, dedupe by `pack_id`, and mark each affected pack as `stale_at = detected_at` in a new `packs.stale_at` column. The coach surface reads `stale_at` and shows a "new evidence available — re-send?" badge.

**Packs are NEVER auto-recompiled by SP3.** The ledger only flags staleness. Whether to actually recompile is the coach's decision (and a UX choice deferred to a later phase). This matters because:

- Recompiling all stale packs on every library bump risks O(N·M) churn.
- A coach may want to keep an old plan stable for an in-progress client (e.g. they're 6 weeks into a 12-week block and changing recommendations now would be confusing).
- The compute cost of unnecessary compile + schedule generation (Claude/GLM) is non-trivial.

---

## §4 Integration with the existing compile path

Two concrete touch points:

**4a) `compile_runner.run_compile()` writes provenance.**

After `compile()` returns the `EvidencePack`, walk `pack.domain_recommendations` and record every surfaced atom + pattern into `pack_provenance`. Each row carries the *current* node hash, so future ledger diffs know "this pack was compiled against atom EA-X at hash A; the current hash is B; therefore this pack is stale."

Pseudocode:

```python
def run_compile(intake_dict, top_k, threshold):
    pack = _compile(intake, db_path=...)
    md = render_markdown(pack, intake=intake)
    # NEW (SP3):
    if _ledger_enabled():
        record_pack_provenance(
            pack_id=pack.compile_metadata.pack_id,
            pack=pack,
            db_path=_db_path(),
            recorded_at=datetime.utcnow().isoformat(),
        )
    return {"json": pack.model_dump(mode="json"), "md": md}
```

A new column `packs.pack_id` (UUID, distinct from the Supabase `packs.id` PK) is added so the compiler-API and Supabase agree on a stable identifier across writes. ASSUMED: we add this UUID to `EvidencePack.compile_metadata` and generate it server-side at compile time.

**4b) Web edge surfaces `stale_at`.**

`web/app/api/intakes/[id]/compile/route.ts` already writes the `packs` row after a successful compile. Add `stale_at: null` on insert. A future Supabase trigger (or a cron polling `library/_change_log.jsonl`) populates `stale_at` when the ledger flags a pack.

The `/clients/[id]/overview` page reads `packs.stale_at` and surfaces a badge if non-null. The Send-to-client button gets a "Re-send updated plan" affordance when stale.

---

## §5 Open questions (explicit TBDs)

| # | Question | Proposed default | Why TBD |
|---|---|---|---|
| Q1 | Where does the canonical pack_id come from — server-side UUID at compile, or the existing Supabase `packs.id`? | Server-side UUID generated in `compile_runner`, mirrored to Supabase. | Round-tripping through Supabase introduces a write dependency on the web edge; UUID lets the compiler stand alone. |
| Q2 | How do we handle pattern *deletions* (atom no longer backs any pattern)? | Hash of `None` for deleted nodes, treated as a "tombstone" change. Pack provenance rows pointing at the deleted node stay; their pack gets flagged stale on the next diff. | Plain deletion would leave dangling provenance and a confusing `?` in the badge text. |
| Q3 | Push-based or pull-based replication into Supabase? | Push: compiler-api writes provenance + change_log rows to Supabase `pack_provenance` + `pack_stale_events` tables on every compile and every ledger diff. | Pull (Supabase polls Fly) is more resilient to Fly outages but requires a daemon. Push is simpler for v1; revisit if Fly reliability becomes an issue. |
| Q4 | Retention policy for `change_log`? | 90 days, rotated weekly. | Long enough to debug a "why is this pack stale?" question; short enough to keep the JSONL files manageable. |
| Q5 | Multi-tenant concerns? | Each coach gets a scoped `library.db` (per-tenant SQLite file). Ledger is per-tenant, no cross-tenant joins. | We're not multi-tenant yet (one shared library for all coaches in the current SaaS plan); this is a forward-compat note for when we let coaches author their own libraries. |
| Q6 | What's a "stale-enough" threshold to nudge the coach? | Surface badge if ≥1 high-impact atom or pattern changed; surface a quieter "minor evidence update" tag for routine-tier-only changes. | Avoids alarm fatigue from minor reviews. Tier is already on every atom/pattern (`tier: high-impact | routine`). |
| Q7 | Does the schedule-generator (`web/lib/schedule/generate.ts`) need to be re-fired when only the pack updates? | Yes — invalidate the cached schedule at `packs/schedule/{pack_id}.json` when the pack hash changes. | Schedule prose references specific pattern/atom IDs that may no longer be in the new pack. |

---

## §6 Non-goals (explicit)

- **No real-time invalidation.** Library bumps happen on the order of days/weeks; eventual consistency at minute scale is fine. No webhooks, no streaming.
- **No automatic pack recompile.** Coach UX decision; defer.
- **No event ingestion from outside the library.** Client-side check-ins, wearables, intake updates — those are SP4+ concerns. SP3 only tracks dependencies *within* the evidence DAG.
- **No tracking of intake → pack edges.** The intake itself isn't versioned; pack provenance captures the library state at compile time, not the intake state.
- **No UI for browsing the change_log.** Internal-only via SQL queries for v1.

---

## §7 Implementation slicing

Three follow-up plans, each its own commit and review cycle:

### SP3.1 — Hashing + node_hashes table (~1 day)

- Migration: `library/migrations/00X_sp3_node_hashes.sql` creating `node_hashes` and `change_log`.
- New module: `src/hcc_compiler/ledger/hashing.py` — canonical projection + sha256.
- New module: `src/hcc_compiler/ledger/diff.py` — walks fresh hashes against `node_hashes`, writes diff rows.
- `scripts/curation/build_index.py` calls `diff_and_write()` after writing atoms/patterns.
- Tests: hash stability under YAML reordering, deletion-as-tombstone, first-seen behavior.

### SP3.2 — Pack provenance writes (~1 day)

- Migration: `library/migrations/00Y_sp3_pack_provenance.sql` creating `pack_provenance`.
- `compile_runner.run_compile()` records provenance after every successful compile.
- New optional field `EvidencePack.compile_metadata.pack_id`.
- Tests: provenance row count matches pack atom + pattern count; provenance hash matches node_hashes row at compile time.

### SP3.3 — Web-side staleness UX (~2 days)

- Supabase migration: add `packs.stale_at TIMESTAMPTZ`.
- Sync job (cron on Fly or Vercel) that reads `library/_change_log.jsonl` + `pack_provenance` and writes `packs.stale_at` to Supabase.
- Web UI: badge on overview page, "Re-send updated plan" affordance on share button.
- Tests: end-to-end — bump library, observe pack flagged, coach sees badge, send-to-client regenerates schedule.

Each slice is independently shippable; SP3.3 unblocks the coach-facing value.

---

## §8 Verification (when implemented)

```bash
# After SP3.1
uv run python scripts/curation/build_index.py library library.db
sqlite3 library.db "SELECT COUNT(*) FROM node_hashes;"  # > 0
sqlite3 library.db "SELECT COUNT(*) FROM change_log WHERE old_hash IS NULL;"  # first-seen rows

# After SP3.2 — compile a persona and check provenance
uv run python scripts/compile_plan.py tests/fixtures/intakes/intake_amy_runner.yaml --db library.db
sqlite3 library.db "SELECT COUNT(*) FROM pack_provenance;"  # > 0

# After SP3.3 — bump an atom, rebuild, confirm Supabase packs.stale_at populated
# (touch any EA-*.yaml's claim field, then rebuild)
uv run python scripts/curation/build_index.py library library.db
# Wait for sync job, then:
curl "https://your-supabase.../rest/v1/packs?stale_at=not.is.null"
```

---

## §9 Risks

- **Hash instability** if the canonical projection misses a volatile field — symptom is flag-storm on every routine atom review. Mitigation: comprehensive `tests/ledger/test_hashing.py` covering every known volatile field.
- **DAG explosion** at large library sizes (>10k atoms). Mitigation: indexes on `pack_provenance.source_node_id` and chunked diff queries.
- **Supabase mirror drift** if push fails. Mitigation: change_log replay endpoint that re-emits a date range on demand.
- **False staleness** from cosmetic pattern edits (re-flowed prose, fixed typo) producing a hash change. Mitigation: explicit `ignore_for_hash:` list in the YAML if it becomes a problem; YAGNI for v1.
