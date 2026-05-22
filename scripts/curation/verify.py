import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
import yaml  # noqa: E402
from hcc_compiler.models import EvidenceAtom  # noqa: E402
from hcc_compiler.citation_gate.orchestrator import verify_atom  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: verify.py <draft.yaml | dir>", file=sys.stderr)
        return 2
    target = Path(sys.argv[1])
    paths = sorted(target.rglob("*.yaml")) if target.is_dir() else [target]
    out_dir = Path("verify-output")
    out_dir.mkdir(parents=True, exist_ok=True)
    any_fail = False
    for p in paths:
        atom = EvidenceAtom.model_validate(yaml.safe_load(p.read_text(encoding="utf-8")))
        result = verify_atom(atom)
        (out_dir / f"{atom.id}.json").write_text(json.dumps(result, indent=2))
        print(f"{atom.id}: {result['overall']}")
        if result["overall"] == "FAIL":
            any_fail = True
    return 1 if any_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
