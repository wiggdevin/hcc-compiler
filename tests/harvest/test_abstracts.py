"""``load_source_texts`` prefers full_text over abstract per candidate."""
import json
from pathlib import Path

from hcc_compiler.harvest.abstracts import load_abstracts, load_source_texts


def test_prefers_full_text_when_present(tmp_path: Path):
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
    assert texts["111"] == "full body A"
    assert texts["10.1/a"] == "full body A"
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
