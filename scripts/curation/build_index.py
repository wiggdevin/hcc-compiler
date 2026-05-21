import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from hcc_compiler.build_index import build_index  # noqa: E402

def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("library")
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("library.db")
    build_index(root, out)
    print(f"Built {out} from {root}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
