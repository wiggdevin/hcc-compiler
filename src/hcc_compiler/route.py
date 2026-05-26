from __future__ import annotations
import json
from pathlib import Path
import yaml


def _id_present_in_library(library_root: Path, atom_id: str) -> bool:
    fname = f"{atom_id}.yaml"
    if (library_root / "queue" / fname).exists():
        return True
    atoms_root = library_root / "atoms"
    if not atoms_root.exists():
        return False
    return any((d / fname).exists() for d in atoms_root.iterdir() if d.is_dir())


def _merge_citation_verdicts(atom: dict, verify: dict) -> None:
    """Mutate ``atom['citations'][i]['existence'/'faithfulness']`` in place
    from the verify-output payload, so library YAMLs carry the gate's
    real verdicts instead of the LLM's placeholder strings."""
    verdicts_by_id = {
        c["id"]: c for c in verify.get("citations", []) if "id" in c
    }
    for cit in atom.get("citations", []):
        v = verdicts_by_id.get(cit.get("id"))
        if v is None:
            continue
        cit["existence"] = v["existence"]
        cit["faithfulness"] = v["faithfulness"]


def route_draft(draft_dir: Path, verify_dir: Path, library_root: Path) -> dict[str, str]:
    """Move each draft YAML into library/atoms/<domain>/ (admitted) or library/queue/ (queued)."""
    decisions: dict[str, str] = {}
    for draft_path in sorted(draft_dir.glob("*.yaml")):
        atom = yaml.safe_load(draft_path.read_text(encoding="utf-8"))
        atom_id = atom["id"]
        verify_path = verify_dir / f"{atom_id}.json"
        if not verify_path.exists():
            decisions[atom_id] = "skipped-no-verify"
            continue
        verify = json.loads(verify_path.read_text(encoding="utf-8"))
        verdict = verify.get("overall")
        _merge_citation_verdicts(atom, verify)
        tier = atom.get("tier")
        if _id_present_in_library(library_root, atom_id):
            decisions[atom_id] = "skipped-collision"
            continue
        if tier == "routine" and verdict == "PASS":
            dest_dir = library_root / "atoms" / atom["domain"]
            decision = "admitted"
        else:
            dest_dir = library_root / "queue"
            decision = "queued"
        dest_dir.mkdir(parents=True, exist_ok=True)
        dest_path = dest_dir / f"{atom_id}.yaml"
        dest_path.write_text(yaml.safe_dump(atom, sort_keys=False))
        draft_path.unlink()
        decisions[atom_id] = decision
    return decisions
