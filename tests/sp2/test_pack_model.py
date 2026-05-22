"""Tests for sp2.pack Pydantic models — SC2."""
from __future__ import annotations
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from hcc_compiler.models import Citation, Domain, EvidenceLevel
from hcc_compiler.sp2.pack import (
    AtomMatch,
    CompileMetadata,
    DomainBlock,
    EvidencePack,
    PatternMatch,
)


# ── helpers ──────────────────────────────────────────────────────────────────

def _citation() -> Citation:
    return Citation(
        id="10.1234/test",
        locator_quote="Protein synthesis was elevated.",
        existence="VERIFIED",
        faithfulness="VERIFIED",
        cited_title="Test Study",
    )


def _atom_match(**kwargs) -> AtomMatch:
    defaults = dict(
        atom_id="EA-NUT-0001",
        similarity=0.85,
        claim="High protein diet supports hypertrophy.",
        citations=[_citation()],
        evidence_level=EvidenceLevel.L1,
        population_match_score=0.9,
        warnings=[],
    )
    defaults.update(kwargs)
    return AtomMatch(**defaults)


def _pattern_match(**kwargs) -> PatternMatch:
    defaults = dict(
        pattern_id="RP-NUT-high-protein",
        similarity=0.75,
        applies_because="Client goal is hypertrophy.",
        parameterization="1.6–2.2 g/kg body weight per day.",
        safety_bounds="Up to 3.0 g/kg considered safe in healthy adults.",
        backing_atom_ids=["EA-NUT-0001", "EA-NUT-0002"],
        warnings=[],
    )
    defaults.update(kwargs)
    return PatternMatch(**defaults)


def _domain_block(**kwargs) -> DomainBlock:
    return DomainBlock(
        patterns=[_pattern_match()],
        atoms=[_atom_match()],
        gaps=[],
        **kwargs,
    )


def _compile_metadata(**kwargs) -> CompileMetadata:
    defaults = dict(
        top_k_per_domain=5,
        applicability_threshold=0.4,
        contraindication_hits=[],
        queries_issued={"nutrition": ["protein intake for hypertrophy"]},
    )
    defaults.update(kwargs)
    return CompileMetadata(**defaults)


def _evidence_pack(**kwargs) -> EvidencePack:
    defaults = dict(
        client_id="client-001",
        library_version="0.1.0",
        compiled_at=datetime(2026, 5, 22, 12, 0, 0, tzinfo=timezone.utc),
        domain_recommendations={Domain.NUTRITION: _domain_block()},
        compile_metadata=_compile_metadata(),
    )
    defaults.update(kwargs)
    return EvidencePack(**defaults)


# ── AtomMatch ────────────────────────────────────────────────────────────────

class TestAtomMatch:
    def test_valid(self):
        atom = _atom_match()
        assert atom.atom_id == "EA-NUT-0001"
        assert atom.similarity == 0.85
        assert atom.population_match_score == 0.9
        assert atom.evidence_level == EvidenceLevel.L1

    def test_json_round_trip(self):
        atom = _atom_match()
        restored = AtomMatch.model_validate_json(atom.model_dump_json())
        assert restored == atom

    def test_similarity_lower_bound(self):
        atom = _atom_match(similarity=-1.0)
        assert atom.similarity == -1.0

    def test_similarity_upper_bound(self):
        atom = _atom_match(similarity=1.0)
        assert atom.similarity == 1.0

    def test_similarity_below_minus_one_rejected(self):
        with pytest.raises(ValidationError):
            _atom_match(similarity=-1.01)

    def test_similarity_above_one_rejected(self):
        with pytest.raises(ValidationError):
            _atom_match(similarity=1.01)

    def test_population_match_score_zero(self):
        atom = _atom_match(population_match_score=0.0)
        assert atom.population_match_score == 0.0

    def test_population_match_score_one(self):
        atom = _atom_match(population_match_score=1.0)
        assert atom.population_match_score == 1.0

    def test_population_match_score_below_zero_rejected(self):
        with pytest.raises(ValidationError):
            _atom_match(population_match_score=-0.01)

    def test_population_match_score_above_one_rejected(self):
        with pytest.raises(ValidationError):
            _atom_match(population_match_score=1.01)

    def test_warnings_default_empty(self):
        atom = AtomMatch(
            atom_id="EA-NUT-0001",
            similarity=0.5,
            claim="Test claim.",
            citations=[_citation()],
            evidence_level=EvidenceLevel.L2,
            population_match_score=0.5,
        )
        assert atom.warnings == []


# ── PatternMatch ─────────────────────────────────────────────────────────────

class TestPatternMatch:
    def test_valid(self):
        pm = _pattern_match()
        assert pm.pattern_id == "RP-NUT-high-protein"
        assert pm.similarity == 0.75

    def test_json_round_trip(self):
        pm = _pattern_match()
        restored = PatternMatch.model_validate_json(pm.model_dump_json())
        assert restored == pm

    def test_similarity_bounds_enforced(self):
        with pytest.raises(ValidationError):
            _pattern_match(similarity=1.5)
        with pytest.raises(ValidationError):
            _pattern_match(similarity=-1.5)

    def test_warnings_default_empty(self):
        pm = PatternMatch(
            pattern_id="RP-NUT-test",
            similarity=0.5,
            applies_because="test",
            parameterization="test",
            safety_bounds="test",
            backing_atom_ids=["EA-NUT-0001"],
        )
        assert pm.warnings == []

    def test_empty_backing_atom_ids(self):
        pm = _pattern_match(backing_atom_ids=[])
        assert pm.backing_atom_ids == []


# ── DomainBlock ───────────────────────────────────────────────────────────────

class TestDomainBlock:
    def test_valid_with_content(self):
        block = _domain_block()
        assert len(block.patterns) == 1
        assert len(block.atoms) == 1

    def test_json_round_trip(self):
        block = _domain_block()
        restored = DomainBlock.model_validate_json(block.model_dump_json())
        assert restored == block

    def test_empty_block_valid(self):
        block = DomainBlock()
        assert block.patterns == []
        assert block.atoms == []
        assert block.gaps == []


# ── CompileMetadata ───────────────────────────────────────────────────────────

class TestCompileMetadata:
    def test_valid(self):
        meta = _compile_metadata()
        assert meta.top_k_per_domain == 5
        assert meta.applicability_threshold == 0.4

    def test_json_round_trip(self):
        meta = _compile_metadata()
        restored = CompileMetadata.model_validate_json(meta.model_dump_json())
        assert restored == meta

    def test_defaults(self):
        meta = CompileMetadata(top_k_per_domain=3, applicability_threshold=0.5)
        assert meta.contraindication_hits == []
        assert meta.queries_issued == {}


# ── EvidencePack ──────────────────────────────────────────────────────────────

class TestEvidencePack:
    def test_valid(self):
        pack = _evidence_pack()
        assert pack.client_id == "client-001"
        assert pack.library_version == "0.1.0"
        assert Domain.NUTRITION in pack.domain_recommendations

    def test_json_round_trip(self):
        pack = _evidence_pack()
        restored = EvidencePack.model_validate_json(pack.model_dump_json())
        assert restored == pack

    def test_empty_pack_valid(self):
        """EvidencePack with no domain blocks validates cleanly."""
        pack = EvidencePack(
            client_id="empty-client",
            library_version="0.1.0",
            compiled_at=datetime(2026, 5, 22, tzinfo=timezone.utc),
            domain_recommendations={},
            compile_metadata=CompileMetadata(
                top_k_per_domain=5,
                applicability_threshold=0.4,
            ),
        )
        assert pack.domain_recommendations == {}

    def test_empty_pack_json_round_trip(self):
        pack = EvidencePack(
            client_id="empty-client",
            library_version="0.1.0",
            compiled_at=datetime(2026, 5, 22, tzinfo=timezone.utc),
            domain_recommendations={},
            compile_metadata=CompileMetadata(
                top_k_per_domain=5,
                applicability_threshold=0.4,
            ),
        )
        restored = EvidencePack.model_validate_json(pack.model_dump_json())
        assert restored == pack

    def test_multiple_domains(self):
        pack = _evidence_pack(
            domain_recommendations={
                Domain.NUTRITION: _domain_block(),
                Domain.TRAINING: DomainBlock(),
                Domain.SUPPLEMENTS: _domain_block(),
            }
        )
        assert len(pack.domain_recommendations) == 3

    def test_domain_key_is_domain_enum(self):
        pack = _evidence_pack()
        for key in pack.domain_recommendations:
            assert isinstance(key, Domain)
