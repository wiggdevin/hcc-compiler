import type { AtomMatch } from "@/lib/data/types";
import { formatPercent } from "@/lib/format";
import { GlassCard } from "./glass-card";
import { EvidenceLevelChip } from "./evidence-level-chip";
import { ScorePill } from "./score-pill";
import { CitationChip } from "./citation-chip";
import { WarningRow } from "./warning-row";

interface Props {
  atom: AtomMatch;
}

export function AtomCard({ atom }: Props) {
  return (
    <GlassCard innerClassName="flex h-full flex-col gap-4 p-6">
      <header className="flex items-start justify-between gap-3">
        <span className="rounded border border-white/10 bg-white/[0.04] px-1.5 py-0.5 font-mono text-[0.6rem] text-zinc-400">
          {atom.atom_id}
        </span>
        <EvidenceLevelChip level={atom.evidence_level} />
      </header>

      <p className="text-sm leading-relaxed text-zinc-200">{atom.claim}</p>

      <div className="mt-auto space-y-3">
        <div className="flex flex-wrap gap-1.5">
          <ScorePill
            label="Sim"
            value={formatPercent(atom.similarity, 0)}
            emphasis
          />
          <ScorePill
            label="Match"
            value={formatPercent(atom.population_match_score, 0)}
          />
          <ScorePill
            label="Cites"
            value={String(atom.citations.length)}
          />
        </div>

        {atom.citations.length > 0 ? (
          <div className="flex flex-wrap gap-1.5">
            {atom.citations.slice(0, 4).map((c, i) => (
              <CitationChip key={`${c.id}-${i}`} citation={c} />
            ))}
            {atom.citations.length > 4 ? (
              <span className="self-center text-[0.6rem] text-zinc-500">
                +{atom.citations.length - 4} more
              </span>
            ) : null}
          </div>
        ) : null}

        {atom.warnings.length > 0 ? <WarningRow warnings={atom.warnings} /> : null}
      </div>
    </GlassCard>
  );
}
