"""SC5 — per-domain top-3 atom uniqueness comparison across 6 test_v2 clients.

For each domain, build {atom_id: [clients_with_atom_in_their_top_3]} and report
how many domains have >=1 atom that is unique to a single client's top-3.
Acceptance bar: at least 2 of 6 clients have a top-3 atom in >=1 domain that no
other test_v2 client has in the same domain's top-3.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLES_DIR = PROJECT_ROOT / "docs" / "examples" / "sp2"
PROOF_PATH = Path(
    "/Users/zero-suminc./Inbox/goal-proof-hcc-burndown/SC5.txt"
)

CLIENT_SLUGS = [
    "bradley",
    "david",
    "jackson_white",
    "sarah_nutrition",
    "sebastian",
    "tori_shaw",
]

DOMAINS = ["nutrition", "training", "conditioning", "supplements", "recovery", "behavioral"]


def load_top3_atoms(client_slug: str) -> dict[str, list[str]]:
    path = EXAMPLES_DIR / f"test_v2_{client_slug}.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    domain_blocks = payload.get("domain_recommendations", {})
    out: dict[str, list[str]] = {}
    for domain in DOMAINS:
        block = domain_blocks.get(domain) or {}
        atoms = block.get("atoms", []) or []
        out[domain] = [a["atom_id"] for a in atoms[:3]]
    return out


def main() -> None:
    per_client_top3: dict[str, dict[str, list[str]]] = {
        c: load_top3_atoms(c) for c in CLIENT_SLUGS
    }
    domain_atom_clients: dict[str, dict[str, list[str]]] = {
        d: defaultdict(list) for d in DOMAINS
    }
    for client, by_domain in per_client_top3.items():
        for domain, atom_ids in by_domain.items():
            for atom_id in atom_ids:
                domain_atom_clients[domain][atom_id].append(client)

    clients_with_uniqueness: set[str] = set()
    domain_uniqueness_count = 0
    lines: list[str] = []
    lines.append("=== SC5 — test_v2 top-3 atom uniqueness audit ===\n")
    lines.append("Clients: " + ", ".join(CLIENT_SLUGS) + "\n")
    lines.append("")

    for domain in DOMAINS:
        unique_atoms = {
            atom_id: clients
            for atom_id, clients in domain_atom_clients[domain].items()
            if len(clients) == 1
        }
        shared_atoms = {
            atom_id: clients
            for atom_id, clients in domain_atom_clients[domain].items()
            if len(clients) >= 2
        }
        lines.append(f"--- {domain.upper()} ---")
        lines.append(f"  unique-to-one-client atoms: {len(unique_atoms)}")
        lines.append(f"  shared-by-2+-clients atoms: {len(shared_atoms)}")
        if unique_atoms:
            domain_uniqueness_count += 1
        for atom_id, clients in sorted(unique_atoms.items()):
            lines.append(f"    [{clients[0]}] {atom_id}")
            clients_with_uniqueness.add(clients[0])
        if shared_atoms:
            lines.append("  shared atoms (>=2 clients):")
            for atom_id, clients in sorted(
                shared_atoms.items(), key=lambda kv: (-len(kv[1]), kv[0])
            ):
                lines.append(f"    [{len(clients)}/6] {atom_id} — {clients}")
        lines.append("")

    lines.append("--- SUMMARY ---")
    lines.append(f"  domains with >=1 unique top-3 atom: {domain_uniqueness_count} / {len(DOMAINS)}")
    lines.append(
        f"  clients with >=1 unique top-3 atom in some domain: "
        f"{len(clients_with_uniqueness)} ({sorted(clients_with_uniqueness)})"
    )
    bar_met = len(clients_with_uniqueness) >= 2
    lines.append(
        f"  ACCEPTANCE BAR (>=2 clients have a unique top-3 in >=1 domain): "
        f"{'MET' if bar_met else 'NOT MET'}"
    )

    output = "\n".join(lines) + "\n"
    PROOF_PATH.parent.mkdir(parents=True, exist_ok=True)
    PROOF_PATH.write_text(output, encoding="utf-8")
    print(output)


if __name__ == "__main__":
    main()
