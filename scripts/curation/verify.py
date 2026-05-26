import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
import yaml  # noqa: E402
from hcc_compiler.models import EvidenceAtom  # noqa: E402
from hcc_compiler.citation_gate.orchestrator import verify_atom  # noqa: E402
from hcc_compiler.harvest.abstracts import load_source_texts  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify draft EvidenceAtoms.")
    parser.add_argument("target", help="draft YAML file or directory")
    parser.add_argument(
        "--harvest",
        default="harvest-output",
        help="directory of harvest JSON files to source abstracts/full text from "
             "(default: harvest-output)",
    )
    args = parser.parse_args()

    target = Path(args.target)
    paths = sorted(target.rglob("*.yaml")) if target.is_dir() else [target]
    source_text_map = load_source_texts(args.harvest)
    out_dir = Path("verify-output")
    out_dir.mkdir(parents=True, exist_ok=True)
    any_fail = False
    for p in paths:
        atom = EvidenceAtom.model_validate(yaml.safe_load(p.read_text(encoding="utf-8")))
        source_texts = {
            c.id: source_text_map[c.id] for c in atom.citations if c.id in source_text_map
        }
        result = verify_atom(atom, source_texts=source_texts)
        (out_dir / f"{atom.id}.json").write_text(json.dumps(result, indent=2))
        print(f"{atom.id}: {result['overall']}")
        if result["overall"] == "FAIL":
            any_fail = True
    return 1 if any_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
