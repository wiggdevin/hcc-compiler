"""``load_source_texts`` concatenates abstract + full_text per candidate."""
import json
from pathlib import Path

from hcc_compiler.harvest.abstracts import load_abstracts, load_source_texts


def test_concatenates_abstract_and_full_text(tmp_path: Path):
    """Both fields must be searchable — meta-analytic quotes are sometimes in
    the abstract but rephrased in the body, and vice versa."""
    (tmp_path / "nutrition-2026.json").write_text(json.dumps([
        {
            "pmid": "111",
            "doi": "10.1/a",
            "abstract": "abstract A",
            "full_text": "full body A",
        },
        {
            "pmid": "222",
            "doi": "10.2/b",
            "abstract": "abstract B",
            "full_text": "",  # paywalled — no PMC
        },
    ]))

    texts = load_source_texts(tmp_path)
    # Both fields present → concatenated, both phrases findable.
    assert "abstract A" in texts["111"]
    assert "full body A" in texts["111"]
    assert texts["10.1/a"] == texts["111"]
    # Only abstract present → abstract alone (no leading newline noise).
    assert texts["222"] == "abstract B"
    assert texts["10.2/b"] == "abstract B"


def test_skips_entries_without_any_text(tmp_path: Path):
    (tmp_path / "x.json").write_text(json.dumps([
        {"pmid": "333", "abstract": "", "full_text": ""},
    ]))
    texts = load_source_texts(tmp_path)
    assert "333" not in texts


def test_load_abstracts_is_backward_compat_alias(tmp_path: Path):
    (tmp_path / "x.json").write_text(json.dumps([
        {"pmid": "444", "abstract": "abstract C", "full_text": "full body C"},
    ]))
    assert load_abstracts(tmp_path) == load_source_texts(tmp_path)
