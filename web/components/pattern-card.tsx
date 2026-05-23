import { ChevronRight, Quote, Layers, ShieldAlert } from "lucide-react";
import type { PatternMatch } from "@/lib/data/types";
import { formatPercent, truncate } from "@/lib/format";
import { GlassCard } from "./glass-card";
import { ScorePill } from "./score-pill";
import { WarningRow } from "./warning-row";

interface Props {
  pattern: PatternMatch;
  defaultOpen?: boolean;
}

export function PatternCard({ pattern, defaultOpen = true }: Props) {
  return (
    <GlassCard emphasis innerClassName="p-8">
      <details open={defaultOpen} className="group flex flex-col gap-6">
        <summary className="flex cursor-pointer list-none flex-col gap-3 select-none [&::-webkit-details-marker]:hidden">
          <div className="flex flex-wrap items-start justify-between gap-3">
            <div className="flex flex-1 items-start gap-3">
              <ChevronRight
                className="mt-1 h-4 w-4 shrink-0 text-zinc-400 transition-transform group-open:rotate-90"
                strokeWidth={1.75}
              />
              <div className="flex flex-col gap-2">
                <span className="rounded border border-white/15 bg-white/[0.06] px-2 py-0.5 font-mono text-[0.65rem] text-zinc-200 self-start">
                  {pattern.pattern_id}
                </span>
                <h3 className="text-xl font-semibold tracking-tight text-white">
                  {pattern.pattern_id.replace(/^RP-/, "").replace(/-/g, " ")}
                </h3>
                <p className="text-[0.7rem] italic leading-snug text-zinc-400 group-open:hidden">
                  {truncate(pattern.applies_because, 140)}
                </p>
              </div>
            </div>
            <div className="flex flex-wrap gap-1.5">
              <ScorePill
                label="Similarity"
                value={formatPercent(pattern.similarity, 0)}
                emphasis
              />
              <ScorePill
                label="Atoms"
                value={String(pattern.backing_atom_ids.length)}
              />
            </div>
          </div>
        </summary>

        <div className="flex flex-col gap-6 pt-2">
          {/* Applies because */}
          <div className="flex gap-3">
            <Quote
              className="h-4 w-4 shrink-0 text-zinc-500"
              strokeWidth={1.5}
            />
            <p className="text-sm italic leading-relaxed text-zinc-200">
              {pattern.applies_because}
            </p>
          </div>

          {/* Parameterization */}
          <div className="flex flex-col gap-2">
            <div className="flex items-center gap-2">
              <Layers className="h-3 w-3 text-zinc-500" strokeWidth={1.5} />
              <p className="text-[0.65rem] font-semibold uppercase tracking-[0.18em] text-zinc-500">
                Parameterization
              </p>
            </div>
            <p className="rounded-md border border-white/[0.06] bg-white/[0.02] px-4 py-3 text-sm leading-relaxed text-zinc-300">
              {pattern.parameterization}
            </p>
          </div>

          {/* Safety bounds */}
          {pattern.safety_bounds ? (
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2">
                <ShieldAlert
                  className="h-3 w-3 text-amber-300/80"
                  strokeWidth={1.5}
                />
                <p className="text-[0.65rem] font-semibold uppercase tracking-[0.18em] text-amber-200/70">
                  Safety bounds
                </p>
              </div>
              <p className="rounded-md border border-amber-400/15 bg-amber-400/[0.03] px-4 py-3 text-sm leading-relaxed text-amber-50/85">
                {pattern.safety_bounds}
              </p>
            </div>
          ) : null}

          {/* Backing atoms */}
          {pattern.backing_atom_ids.length > 0 ? (
            <div className="flex flex-col gap-2">
              <p className="text-[0.65rem] font-semibold uppercase tracking-[0.18em] text-zinc-500">
                Backed by {pattern.backing_atom_ids.length} atom
                {pattern.backing_atom_ids.length === 1 ? "" : "s"}
              </p>
              <div className="flex flex-wrap gap-1.5">
                {pattern.backing_atom_ids.slice(0, 10).map((id) => (
                  <span
                    key={id}
                    className="rounded border border-white/[0.08] bg-white/[0.02] px-2 py-0.5 font-mono text-[0.6rem] text-zinc-400"
                  >
                    {id}
                  </span>
                ))}
                {pattern.backing_atom_ids.length > 10 ? (
                  <span className="self-center text-[0.6rem] text-zinc-500">
                    +{pattern.backing_atom_ids.length - 10} more
                  </span>
                ) : null}
              </div>
            </div>
          ) : null}

          {pattern.warnings.length > 0 ? (
            <WarningRow warnings={pattern.warnings} />
          ) : null}
        </div>
      </details>
    </GlassCard>
  );
}
