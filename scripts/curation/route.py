import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from hcc_compiler.route import route_draft  # noqa: E402


def main() -> int:
    draft_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("draft-output")
    verify_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("verify-output")
    library_root = Path(sys.argv[3]) if len(sys.argv) > 3 else Path("library")
    decisions = route_draft(draft_dir, verify_dir, library_root)
    for aid, decision in decisions.items():
        print(f"{aid}: {decision}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
