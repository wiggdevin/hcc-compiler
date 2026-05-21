# scripts/curation/validate_library.py
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))
from hcc_compiler.validate import validate_library  # noqa: E402

def main() -> int:
    root = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("library")
    problems = validate_library(root)
    if problems:
        print(f"LIBRARY INVALID — {len(problems)} problem(s):")
        for p in problems:
            print(f"  - {p}")
        return 1
    print("LIBRARY OK")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
