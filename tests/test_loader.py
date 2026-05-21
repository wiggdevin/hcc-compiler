from pathlib import Path
import yaml
from hcc_compiler.models import EvidenceAtom
from hcc_compiler.loader import load_dir
from tests.test_models_atom import VALID  # reuse the valid atom fixture

def _write(p: Path, data: dict):
    p.write_text(yaml.safe_dump(data))

def test_loads_valid_records(tmp_path):
    _write(tmp_path / "a1.yaml", VALID)
    _write(tmp_path / "a2.yaml", {**VALID, "id": "EA-NUT-0002"})
    records, errors = load_dir(tmp_path, EvidenceAtom)
    assert len(records) == 2
    assert errors == []

def test_invalid_file_reported_with_path(tmp_path):
    _write(tmp_path / "good.yaml", VALID)
    _write(tmp_path / "bad.yaml", {**VALID, "id": "nope"})
    records, errors = load_dir(tmp_path, EvidenceAtom)
    assert len(records) == 1
    assert len(errors) == 1
    assert "bad.yaml" in errors[0].path
