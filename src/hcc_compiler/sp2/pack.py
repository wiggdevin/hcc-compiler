from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel, Field

from hcc_compiler.models import Domain, EvidenceLevel, Citation


class AtomMatch(BaseModel):
    atom_id: str
    similarity: float = Field(ge=-1.0, le=1.0)
    claim: str
    citations: list[Citation]
    evidence_level: EvidenceLevel
    population_match_score: float = Field(ge=0.0, le=1.0)
    warnings: list[str] = Field(default_factory=list)


class PatternMatch(BaseModel):
    pattern_id: str
    similarity: float = Field(ge=-1.0, le=1.0)
    applies_because: str
    parameterization: str
    safety_bounds: str
    backing_atom_ids: list[str]
    warnings: list[str] = Field(default_factory=list)


class DomainBlock(BaseModel):
    patterns: list[PatternMatch] = Field(default_factory=list)
    atoms: list[AtomMatch] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)


class CompileMetadata(BaseModel):
    top_k_per_domain: int
    applicability_threshold: float
    contraindication_hits: list[str] = Field(default_factory=list)
    queries_issued: dict[str, list[str]] = Field(default_factory=dict)


class EvidencePack(BaseModel):
    client_id: str
    library_version: str
    compiled_at: datetime
    domain_recommendations: dict[Domain, DomainBlock] = Field(default_factory=dict)
    compile_metadata: CompileMetadata
