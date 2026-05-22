from __future__ import annotations
from datetime import date
from enum import Enum
from pydantic import BaseModel, Field


class EvidenceLevel(str, Enum):
    L1 = "L1"; L2 = "L2"; L3 = "L3"; L4 = "L4"


class Tier(str, Enum):
    HIGH_IMPACT = "high-impact"
    ROUTINE = "routine"


class Domain(str, Enum):
    NUTRITION = "nutrition"
    TRAINING = "training"
    CONDITIONING = "conditioning"
    SUPPLEMENTS = "supplements"
    RECOVERY = "recovery"
    BEHAVIORAL = "behavioral"


class Citation(BaseModel):
    id: str                 # DOI or PMID
    locator_quote: str      # verbatim supporting passage
    existence: str          # VERIFIED / PLAUSIBLE / UNVERIFIABLE / DOI_MISMATCH / FABRICATED
    faithfulness: str       # VERIFIED / MINOR_DISTORTION / MAJOR_DISTORTION / UNSUPPORTED / ACCESS_LIMITED
    cited_title: str | None = None  # NEW: the title the citation claims, used for L1 DOI_MISMATCH detection


class PopulationApplicability(BaseModel):
    age: str
    sex: str
    training_status: str
    dose_magnitude: str
    duration: str


class EvidenceAtom(BaseModel):
    id: str = Field(pattern=r"^EA-[A-Z]{2,4}-\d{4}$")
    domain: Domain
    claim: str
    evidence_level: EvidenceLevel
    citations: list[Citation] = Field(min_length=1)
    population_applicability: PopulationApplicability
    effect: str
    contraindications: list[str] = Field(default_factory=list)
    tier: Tier
    approval: str
    library_version: str
    last_reviewed: date
    expiry: date


class RecommendationPattern(BaseModel):
    id: str = Field(pattern=r"^RP-[A-Z]{2,4}-[a-z0-9-]+$")
    domain: Domain
    pattern: str
    parameterization: str
    backing_atom_ids: list[str] = Field(min_length=1)
    falsification_signal: str
    safety_bounds: str
    applies_because: str
    doesnt_apply_if: str
    tier: Tier
    approval: str
    version: str
