import { ChevronRight } from "lucide-react";
import type { AtomMatch, EvidenceLevel, EvidencePack } from "@/lib/data/types";
import { domainConfidences } from "@/lib/scoring";
import { DOMAIN_META } from "@/lib/data/domains";
import { formatPercent } from "@/lib/format";
import { GlassCard } from "./glass-card";

interface Props {
  pack: EvidencePack;
}

function median(xs: number[]): number {
  if (xs.length === 0) return 0;
  const sorted = [...xs].sort((a, b) => a - b);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 === 0
    ? (sorted[mid - 1] + sorted[mid]) / 2
    : sorted[mid];
}

function allAtoms(pack: EvidencePack): AtomMatch[] {
  return Object.values(pack.domain_recommendations).flatMap((b) => b.atoms);
}

function patternCount(pack: EvidencePack): number {
  return Object.values(pack.domain_recommendations).reduce(
    (sum, b) => sum + b.patterns.length,
    0,
  );
}

/**
 * Anti-inflation surface. Shows the raw evidence distribution + per-domain
 * thin-coverage flags so the headline confidence never hides what's behind it.
 */
export function ScoreExplainer({ pack }: Props) {
  const atoms = allAtoms(pack);
  const dist: Record<EvidenceLevel, number> = { L1: 0, L2: 0, L3: 0, L4: 0 };
  for (const a of atoms) {
    dist[a.evidence_level] = (dist[a.evidence_level] ?? 0) + 1;
  }

  const medSim = median(atoms.map((a) => a.similarity));
  const medPop = median(atoms.map((a) => a.population_match_score));

  const rows = domainConfidences(pack);
  const thin = rows.filter((r) => r.confidence < 0.6);

  const totalPatterns = patternCount(pack);

  return (
    <GlassCard innerClassName="px-5 py-4">
      <details className="group">
        <summary className="flex cursor-pointer list-none items-center gap-2 select-none">
          <ChevronRight
            className="h-3.5 w-3.5 text-zinc-400 transition-transform group-open:rotate-90"
            strokeWidth={1.75}
          />
          <span className="text-[0.65rem] font-semibold uppercase tracking-[0.18em] text-zinc-300">
            Why this score
          </span>
        </summary>

        <div className="mt-4 flex flex-col gap-4">
          {/* Evidence distribution */}
          <div className="flex flex-col gap-1.5">
            <p className="text-[0.55rem] font-medium uppercase tracking-wider text-zinc-500">
              Evidence distribution
            </p>
            <div className="flex flex-wrap gap-2 font-mono text-[0.7rem] text-zinc-200">
              <span>L1: {dist.L1}</span>
              <span className="text-zinc-600">·</span>
              <span>L2: {dist.L2}</span>
              <span className="text-zinc-600">·</span>
              <span>L3: {dist.L3}</span>
              <span className="text-zinc-600">·</span>
              <span>L4: {dist.L4}</span>
            </div>
          </div>

          {/* Median similarity / pop_match */}
          <div className="flex flex-col gap-1.5">
            <p className="text-[0.55rem] font-medium uppercase tracking-wider text-zinc-500">
              Medians across atoms
            </p>
            <div className="flex flex-wrap gap-3 font-mono text-[0.7rem] text-zinc-200">
              <span>
                <span className="text-zinc-500">similarity</span>{" "}
                {formatPercent(medSim, 0)}
              </span>
              <span className="text-zinc-600">·</span>
              <span>
                <span className="text-zinc-500">pop_match</span>{" "}
                {formatPercent(medPop, 0)}
              </span>
            </div>
          </div>

          {/* Thin coverage rows */}
          {thin.length > 0 ? (
            <div className="flex flex-col gap-1.5">
              <p className="text-[0.55rem] font-medium uppercase tracking-wider text-amber-200/70">
                Thin coverage
              </p>
              <div className="flex flex-col gap-1">
                {thin.map((r) => {
                  const meta = DOMAIN_META[r.domain];
                  const Icon = meta.icon;
                  return (
                    <div
                      key={r.domain}
                      data-thin-coverage="true"
                      className="flex items-center gap-2 rounded-md border border-amber-400/15 bg-amber-400/[0.04] px-2.5 py-1.5"
                    >
                      <Icon
                        className="h-3 w-3 text-amber-300"
                        strokeWidth={1.5}
                      />
                      <span className="text-[0.7rem] text-amber-50/90">
                        {meta.label}
                      </span>
                      <span className="font-mono text-[0.65rem] text-amber-200/70">
                        {formatPercent(r.confidence, 0)}
                      </span>
                      <span className="ml-auto text-[0.6rem] italic text-amber-200/60">
                        thin coverage
                      </span>
                    </div>
                  );
                })}
              </div>
            </div>
          ) : null}

          {/* Caption */}
          <p className="text-[0.65rem] italic text-zinc-500">
            Based on {atoms.length} atom{atoms.length === 1 ? "" : "s"} and{" "}
            {totalPatterns} pattern{totalPatterns === 1 ? "" : "s"} from library
            v{pack.library_version}.
          </p>
        </div>
      </details>
    </GlassCard>
  );
}
