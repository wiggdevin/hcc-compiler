import type {
  AtomMatch,
  Citation,
  Domain,
  DomainBlock,
  EvidenceLevel,
  EvidencePack,
} from "./data/types";
import { DOMAIN_ORDER } from "./data/domains";

const EVIDENCE_WEIGHT: Record<EvidenceLevel, number> = {
  L1: 1.0,
  L2: 0.85,
  L3: 0.7,
  L4: 0.55,
};

function mean(xs: number[]): number {
  if (xs.length === 0) return 0;
  return xs.reduce((a, b) => a + b, 0) / xs.length;
}

/**
 * Per-atom confidence: applicability × evidence weight × similarity.
 * Similarity gets a soft weight (0.5 floor) so a perfectly applicable
 * L1 result with mediocre cosine still scores well.
 */
export function atomConfidence(atom: AtomMatch): number {
  const ev = EVIDENCE_WEIGHT[atom.evidence_level] ?? 0.55;
  const sim = Math.max(0.5, atom.similarity); // soft floor
  return atom.population_match_score * ev * sim;
}

export function domainConfidence(block: DomainBlock): number {
  const atomScores = block.atoms.map(atomConfidence);
  const patternScore = mean(block.patterns.map((p) => p.similarity));
  // If there are no atoms, fall back to patterns; if neither, zero.
  if (atomScores.length === 0 && block.patterns.length === 0) return 0;
  if (atomScores.length === 0) return patternScore;
  // Patterns inform but don't dominate — 70 / 30 split
  return mean(atomScores) * 0.7 + patternScore * 0.3;
}

export interface DomainConfidence {
  domain: Domain;
  confidence: number; // 0..1
  atomCount: number;
  patternCount: number;
}

export function domainConfidences(pack: EvidencePack): DomainConfidence[] {
  return DOMAIN_ORDER.map((d) => {
    const block = pack.domain_recommendations[d];
    return {
      domain: d,
      confidence: domainConfidence(block),
      atomCount: block.atoms.length,
      patternCount: block.patterns.length,
    };
  });
}

export function overallConfidence(pack: EvidencePack): number {
  const rows = domainConfidences(pack);
  let weightedSum = 0;
  let totalWeight = 0;
  for (const r of rows) {
    // Weight by total record count (atoms + patterns ×2 since patterns carry more)
    const w = r.atomCount + r.patternCount * 2;
    weightedSum += r.confidence * w;
    totalWeight += w;
  }
  if (totalWeight === 0) return 0;
  return weightedSum / totalWeight;
}

export interface CitationStats {
  total: number;
  verifiedExistence: number;
  verifiedFaithfulness: number;
  fullyVerified: number;
  integrity: number; // 0..1
}

export function collectCitations(pack: EvidencePack): Citation[] {
  const out: Citation[] = [];
  for (const block of Object.values(pack.domain_recommendations)) {
    for (const a of block.atoms) out.push(...a.citations);
  }
  return out;
}

export function citationStats(pack: EvidencePack): CitationStats {
  const cits = collectCitations(pack);
  const total = cits.length;
  const verifiedExistence = cits.filter((c) => c.existence === "VERIFIED").length;
  const verifiedFaithfulness = cits.filter(
    (c) => c.faithfulness === "VERIFIED",
  ).length;
  const fullyVerified = cits.filter(
    (c) => c.existence === "VERIFIED" && c.faithfulness === "VERIFIED",
  ).length;
  const integrity = total === 0 ? 0 : fullyVerified / total;
  return {
    total,
    verifiedExistence,
    verifiedFaithfulness,
    fullyVerified,
    integrity,
  };
}

export function uniqueCitations(pack: EvidencePack): {
  citation: Citation;
  referencedBy: string[]; // atom_ids
}[] {
  const dedup = new Map<string, { citation: Citation; refs: Set<string> }>();
  for (const block of Object.values(pack.domain_recommendations)) {
    for (const atom of block.atoms) {
      for (const c of atom.citations) {
        const key = c.id;
        const entry = dedup.get(key);
        if (entry) {
          entry.refs.add(atom.atom_id);
        } else {
          dedup.set(key, {
            citation: c,
            refs: new Set([atom.atom_id]),
          });
        }
      }
    }
  }
  return Array.from(dedup.values()).map((e) => ({
    citation: e.citation,
    referencedBy: Array.from(e.refs).sort(),
  }));
}
