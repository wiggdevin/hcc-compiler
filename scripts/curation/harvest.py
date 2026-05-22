import argparse
import json
import sys
from datetime import date
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from hcc_compiler.harvest.queries import DOMAIN_QUERIES, run_harvest  # noqa: E402


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--domain", required=True, choices=sorted(DOMAIN_QUERIES.keys()))
    p.add_argument("--since", type=int, default=2022)
    args = p.parse_args()
    results = run_harvest(args.domain, args.since)
    out_dir = Path("harvest-output")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{args.domain}-{date.today().isoformat()}.json"
    out_path.write_text(json.dumps(results, indent=2))
    print(f"Wrote {len(results)} candidates to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
