/**
 * TypeScript mirror of `src/hcc_compiler/sp2/pack.py` + `models.py`.
 * Tracks the *rendered* JSON shape on disk (some Python-side fields are not
 * serialized into the EvidencePack output).
 */

export const DOMAINS = [
  "nutrition",
  "training",
  "conditioning",
  "supplements",
  "recovery",
  "behavioral",
] as const;
export type Domain = (typeof DOMAINS)[number];

export type EvidenceLevel = "L1" | "L2" | "L3" | "L4";

export type ExistenceVerdict =
  | "VERIFIED"
  | "PLAUSIBLE"
  | "UNVERIFIABLE"
  | "DOI_MISMATCH"
  | "FABRICATED";

export type FaithfulnessVerdict =
  | "VERIFIED"
  | "MINOR_DISTORTION"
  | "MAJOR_DISTORTION"
  | "UNSUPPORTED"
  | "ACCESS_LIMITED";

export interface Citation {
  id: string;
  locator_quote: string;
  existence: ExistenceVerdict;
  faithfulness: FaithfulnessVerdict;
  cited_title?: string;
}

export interface AtomMatch {
  atom_id: string;
  similarity: number;
  claim: string;
  citations: Citation[];
  evidence_level: EvidenceLevel;
  population_match_score: number;
  warnings: string[];
}

export interface PatternMatch {
  pattern_id: string;
  similarity: number;
  applies_because: string;
  parameterization: string;
  safety_bounds: string;
  backing_atom_ids: string[];
  warnings: string[];
}

export interface DomainBlock {
  patterns: PatternMatch[];
  atoms: AtomMatch[];
  gaps?: string[];
}

export interface PreemptiveHit {
  record_id: string;
  record_type: "atom" | "pattern";
  claim_or_summary: string;
  matched_needle: string;
}

export interface CompileMetadata {
  top_k_per_domain: number;
  applicability_threshold: number;
  contraindication_hits: string[];
  preemptive_contraindications: PreemptiveHit[];
  queries_issued: Record<string, string[]>;
}

export interface EvidencePack {
  client_id: string;
  library_version: string;
  compiled_at: string;
  domain_recommendations: Record<Domain, DomainBlock>;
  compile_metadata: CompileMetadata;
}

/* ----------------------------- Intake (YAML) ----------------------------- */

export type Sex = "M" | "F" | "other";
export type TrainingStatus =
  | "untrained"
  | "recreational"
  | "trained"
  | "competitive";
export type Goal =
  | "hypertrophy"
  | "strength"
  | "endurance"
  | "weight_loss"
  | "recomposition"
  | "performance"
  | "longevity";

export interface Demographics {
  age: number;
  sex: Sex;
  weight_kg: number;
  height_cm: number;
}

export interface Constraint {
  type: string;
  detail: string;
}

export interface ClientIntake {
  client_id: string;
  library_version: string;
  demographics: Demographics;
  training_status: TrainingStatus;
  goals: Goal[];
  current_regimen?: string;
  constraints: Constraint[];
  contraindications: string[];
  metabolic_calibration?: number | null;
}
