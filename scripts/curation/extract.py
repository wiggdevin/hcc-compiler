import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
import yaml  # noqa: E402
from hcc_compiler.extract import extract_atom  # noqa: E402


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: extract.py <harvest-output.json>", file=sys.stderr)
        return 2
    candidates = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    out_dir = Path("draft-output")
    out_dir.mkdir(parents=True, exist_ok=True)
    for cand in candidates:
        try:
            draft = extract_atom(cand)
        except Exception as e:
            print(f"skip {cand.get('pmid')}: {e}", file=sys.stderr)
            continue
        (out_dir / f"{draft['id']}.yaml").write_text(yaml.safe_dump(draft, sort_keys=False))
        print(f"wrote {draft['id']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
