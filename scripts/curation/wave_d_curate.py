"""Wave D one-shot curation driver.

Runs three sub-curations (SC7 iron/ferritin, SC8 cycle-aware nutrition,
SC9 age-40+ anabolic resistance) against custom PubMed queries WITHOUT
touching `DOMAIN_QUERIES`. Routes verified atoms straight into the library.

Per-SC artifacts land in ~/Inbox/goal-proof-hcc-burndown/SC{7,8,9}.txt
"""
from __future__ import annotations

import json
import os
import sys
import traceback
from datetime import date
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO / "src"))

import yaml  # noqa: E402

from hcc_compiler.citation_gate.orchestrator import verify_atom  # noqa: E402
from hcc_compiler.extract import extract_atom  # noqa: E402
from hcc_compiler.harvest.abstracts import load_abstracts  # noqa: E402
from hcc_compiler.harvest.queries import _esearch, _summary, build_query  # noqa: E402
from hcc_compiler.models import EvidenceAtom  # noqa: E402
from hcc_compiler.route import route_draft  # noqa: E402


SC_PLANS: dict[str, dict] = {
    "SC7": {
        "label": "iron/ferritin under deficit/training",
        "since": 2018,
        "queries": [
            "iron deficiency athletes systematic review",
            "ferritin endurance trained meta-analysis",
            "iron supplementation deficit systematic review",
            "ferritin depletion exercise meta-analysis",
        ],
        # Atom must land in nutrition/ or supplements/
        "allowed_domains": {"nutrition", "supplements"},
        # Required: population_applicability.training_status covers "trained"
        "guard": lambda atom: "trained" in (atom.population_applicability.training_status or "").lower(),
        "guard_desc": "training_status contains 'trained'",
    },
    "SC8": {
        "label": "cycle-aware nutrition",
        "since": 2015,
        "queries": [
            "menstrual cycle macronutrient meta-analysis",
            "luteal phase carbohydrate systematic review",
            "follicular protein women athletes",
            "premenstrual energy intake meta-analysis",
        ],
        "allowed_domains": {"nutrition"},
        "guard": lambda atom: any(
            tok in (atom.population_applicability.sex or "").lower()
            for tok in ("women", "female")
        ),
        "guard_desc": "sex contains 'women' or 'female'",
    },
    "SC9": {
        "label": "age-40+ anabolic resistance",
        "since": 2015,
        "queries": [
            "anabolic resistance older adults meta-analysis",
            "per-meal protein elderly systematic review",
            "leucine threshold aging muscle",
            "protein dose response older adults",
        ],
        "allowed_domains": {"nutrition", "supplements"},
        "guard": lambda atom: any(
            tok in (atom.population_applicability.age or "").lower()
            for tok in ("older", "40+", ">=40", "elderly")
        ),
        "guard_desc": "age contains 'older adults' / '40+' / '>=40' / 'elderly'",
    },
}


PROOF_DIR = Path.home() / "Inbox" / "goal-proof-hcc-burndown"
PROOF_DIR.mkdir(parents=True, exist_ok=True)


def harvest_for_sc(sc_id: str, plan: dict, proof: list[str]) -> list[dict]:
    """Run custom queries, return deduped candidate dicts."""
    proof.append(f"=== Queries ({len(plan['queries'])}) ===")
    seen: set[str] = set()
    out: list[dict] = []
    for base in plan["queries"]:
        q = build_query(base, plan["since"])
        proof.append(f"  Q: {base}")
        try:
            pmids = _esearch(q)
        except Exception as exc:
            proof.append(f"    ESEARCH FAIL: {exc!r}")
            raise
        proof.append(f"    {len(pmids)} pmids")
        for pmid in pmids:
            if pmid in seen:
                continue
            seen.add(pmid)
            try:
                summary = _summary(pmid)
            except Exception as exc:
                proof.append(f"    SUMMARY FAIL pmid={pmid}: {exc!r}")
                continue
            if not summary.get("abstract"):
                continue
            out.append(summary)
    proof.append(f"=== Harvest total: {len(out)} candidates with abstracts ===")
    return out


def write_harvest_snapshot(sc_id: str, candidates: list[dict]) -> Path:
    """Append candidates to a harvest-output JSON so verify can load abstracts."""
    harvest_dir = REPO / "harvest-output"
    harvest_dir.mkdir(parents=True, exist_ok=True)
    out_path = harvest_dir / f"wave-d-{sc_id.lower()}-{date.today().isoformat()}.json"
    out_path.write_text(json.dumps(candidates, indent=2))
    return out_path


def extract_drafts(candidates: list[dict], proof: list[str]) -> list[Path]:
    draft_dir = REPO / "draft-output"
    draft_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    proof.append(f"=== Extraction (n={len(candidates)}) ===")
    for cand in candidates:
        try:
            draft = extract_atom(cand)
        except Exception as exc:
            proof.append(f"  EXTRACT FAIL pmid={cand.get('pmid')}: {exc!r}")
            continue
        path = draft_dir / f"{draft['id']}.yaml"
        path.write_text(yaml.safe_dump(draft, sort_keys=False))
        proof.append(f"  wrote draft {draft['id']} (pmid={cand.get('pmid')}, domain={draft.get('domain')})")
        written.append(path)
    proof.append(f"=== Drafts written: {len(written)} ===")
    return written


def verify_drafts(draft_paths: list[Path], proof: list[str]) -> dict[str, str]:
    """Verify each draft. Returns {atom_id: overall_verdict}. Writes JSON to verify-output/."""
    verify_dir = REPO / "verify-output"
    verify_dir.mkdir(parents=True, exist_ok=True)
    abstracts = load_abstracts(REPO / "harvest-output")
    results: dict[str, str] = {}
    proof.append(f"=== Verification (n={len(draft_paths)}) ===")
    for p in draft_paths:
        try:
            atom = EvidenceAtom.model_validate(yaml.safe_load(p.read_text(encoding="utf-8")))
        except Exception as exc:
            proof.append(f"  SCHEMA FAIL {p.name}: {exc!r}")
            continue
        source_texts = {c.id: abstracts[c.id] for c in atom.citations if c.id in abstracts}
        result = verify_atom(atom, source_texts=source_texts)
        (verify_dir / f"{atom.id}.json").write_text(json.dumps(result, indent=2))
        overall = result["overall"]
        results[atom.id] = overall
        cit_lines = [f"      {c['id']}: existence={c['existence']} faithfulness={c['faithfulness']}" for c in result["citations"]]
        proof.append(f"  {atom.id}: {overall}")
        proof.extend(cit_lines)
    return results


def filter_routable_drafts(plan: dict, draft_paths: list[Path], verdicts: dict[str, str], proof: list[str]) -> list[Path]:
    """Keep only drafts whose domain matches the SC's allowed_domains AND pass the guard predicate.

    Drafts that don't satisfy those gates are removed from draft-output so route.py
    won't even consider them. Verify outcome (PASS / PASS_WITH_NOTES / FAIL) is route.py's job.
    """
    proof.append(f"=== Domain + applicability gate (allowed={sorted(plan['allowed_domains'])}, guard={plan['guard_desc']}) ===")
    survivors: list[Path] = []
    for p in draft_paths:
        try:
            atom = EvidenceAtom.model_validate(yaml.safe_load(p.read_text(encoding="utf-8")))
        except Exception as exc:
            proof.append(f"  GATE-DROP {p.name}: schema_invalid {exc!r}")
            p.unlink(missing_ok=True)
            continue
        if atom.domain.value not in plan["allowed_domains"]:
            proof.append(f"  GATE-DROP {atom.id}: domain={atom.domain.value} not in allowed set")
            p.unlink(missing_ok=True)
            continue
        if not plan["guard"](atom):
            proof.append(
                f"  GATE-DROP {atom.id}: guard FAIL "
                f"(age={atom.population_applicability.age!r} sex={atom.population_applicability.sex!r} "
                f"training_status={atom.population_applicability.training_status!r})"
            )
            p.unlink(missing_ok=True)
            continue
        verdict = verdicts.get(atom.id, "MISSING")
        proof.append(f"  GATE-KEEP {atom.id}: domain={atom.domain.value} verdict={verdict}")
        survivors.append(p)
    return survivors


def route_survivors(proof: list[str]) -> dict[str, str]:
    """Route remaining drafts. Returns route.py's decision dict."""
    decisions = route_draft(
        draft_dir=REPO / "draft-output",
        verify_dir=REPO / "verify-output",
        library_root=REPO / "library",
    )
    proof.append(f"=== Routing decisions ===")
    for aid, decision in decisions.items():
        proof.append(f"  {aid}: {decision}")
    return decisions


def run_sc(sc_id: str, plan: dict) -> dict:
    """Run one sub-curation end-to-end. Returns summary dict."""
    proof: list[str] = []
    proof.append(f"### {sc_id} — {plan['label']} ###")
    proof.append(f"date: {date.today().isoformat()}")
    summary: dict = {"sc_id": sc_id, "label": plan["label"], "admitted": [], "queued": [], "frozen": False, "freeze_reason": None}
    try:
        candidates = harvest_for_sc(sc_id, plan, proof)
        if not candidates:
            proof.append("NO CANDIDATES — freezing SC")
            summary["frozen"] = True
            summary["freeze_reason"] = "no_pubmed_candidates"
            return summary
        write_harvest_snapshot(sc_id, candidates)
    except Exception as exc:
        proof.append(f"HARVEST PHASE FAILED: {exc!r}\n{traceback.format_exc()}")
        summary["frozen"] = True
        summary["freeze_reason"] = f"harvest_error: {exc!r}"
        return summary
    finally:
        # We always want partial proof on disk.
        pass

    try:
        draft_paths = extract_drafts(candidates, proof)
    except Exception as exc:
        proof.append(f"EXTRACT PHASE FAILED: {exc!r}\n{traceback.format_exc()}")
        summary["frozen"] = True
        summary["freeze_reason"] = f"extract_error: {exc!r}"
        return summary

    if not draft_paths:
        proof.append("NO DRAFTS extracted — freezing SC")
        summary["frozen"] = True
        summary["freeze_reason"] = "no_drafts_extracted"
        return summary

    verdicts = verify_drafts(draft_paths, proof)

    survivors = filter_routable_drafts(plan, draft_paths, verdicts, proof)
    if not survivors:
        proof.append("NO DRAFTS survived applicability gate — freezing SC")
        summary["frozen"] = True
        summary["freeze_reason"] = "no_drafts_passed_applicability_gate"
        return summary

    decisions = route_survivors(proof)
    for aid, dec in decisions.items():
        if dec == "admitted":
            summary["admitted"].append(aid)
        elif dec == "queued":
            summary["queued"].append(aid)

    if not summary["admitted"]:
        proof.append("NO ATOMS ADMITTED — freezing SC (verify failed or tier=high-impact)")
        summary["frozen"] = True
        summary["freeze_reason"] = "no_admitted_atoms"

    return summary, proof  # type: ignore[return-value]


def _flush_proof(sc_id: str, proof: list[str]) -> Path:
    out = PROOF_DIR / f"{sc_id}.txt"
    out.write_text("\n".join(proof) + "\n")
    return out


def main() -> int:
    # Sanity: extraction requires both flags.
    if os.environ.get("HCC_LIVE_HTTP", "") != "1":
        print("ERROR: set HCC_LIVE_HTTP=1", file=sys.stderr)
        return 2
    if os.environ.get("HCC_LIVE_LLM", "") != "1":
        print("ERROR: set HCC_LIVE_LLM=1", file=sys.stderr)
        return 2
    if not os.environ.get("ANTHROPIC_AUTH_TOKEN"):
        print("ERROR: set ANTHROPIC_AUTH_TOKEN (e.g. =ZAI_API_KEY for Pattern B)", file=sys.stderr)
        return 2

    grand: dict[str, dict] = {}
    for sc_id, plan in SC_PLANS.items():
        print(f"\n>>> {sc_id}: {plan['label']}")
        proof: list[str] = []
        try:
            res = run_sc(sc_id, plan)
            if isinstance(res, tuple):
                summary, proof = res
            else:
                summary = res
        except SystemExit:
            raise
        except Exception as exc:
            summary = {"sc_id": sc_id, "label": plan["label"], "admitted": [], "queued": [],
                       "frozen": True, "freeze_reason": f"unhandled: {exc!r}"}
            proof.append(f"UNHANDLED: {exc!r}\n{traceback.format_exc()}")
        grand[sc_id] = summary
        proof_path = _flush_proof(sc_id, proof)
        print(f"  proof -> {proof_path}")
        print(f"  admitted: {summary['admitted']}")
        print(f"  queued:   {summary['queued']}")
        if summary["frozen"]:
            print(f"  FROZEN: {summary['freeze_reason']}")

    # Final summary
    print("\n=== Wave D summary ===")
    for sc, s in grand.items():
        status = "FROZEN" if s["frozen"] else "OK"
        print(f"  {sc}: {status}  admitted={s['admitted']}  queued={s['queued']}  reason={s['freeze_reason']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
