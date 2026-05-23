import { notFound } from "next/navigation";
import { ExternalLink } from "lucide-react";
import { getPersona } from "@/lib/data/personas";
import { loadEvidencePack } from "@/lib/data/loader";
import {
  citationStats,
  uniqueCitations,
} from "@/lib/scoring";
import {
  citationHref,
  citationKind,
  formatPercent,
  truncate,
} from "@/lib/format";
import { SectionHeader } from "@/components/section-header";
import { GlassCard } from "@/components/glass-card";
import { ScoreCluster } from "@/components/score-cluster";
import type {
  ExistenceVerdict,
  FaithfulnessVerdict,
} from "@/lib/data/types";
import { cn } from "@/lib/utils";

const EXISTENCE_DOT: Record<ExistenceVerdict, string> = {
  VERIFIED: "bg-emerald-400",
  PLAUSIBLE: "bg-amber-300",
  UNVERIFIABLE: "bg-zinc-500",
  DOI_MISMATCH: "bg-rose-400",
  FABRICATED: "bg-rose-500",
};

const FAITHFULNESS_DOT: Record<FaithfulnessVerdict, string> = {
  VERIFIED: "bg-emerald-400",
  MINOR_DISTORTION: "bg-amber-300",
  MAJOR_DISTORTION: "bg-orange-400",
  UNSUPPORTED: "bg-rose-400",
  ACCESS_LIMITED: "bg-zinc-500",
};

const EXISTENCE_LABEL: Record<ExistenceVerdict, string> = {
  VERIFIED: "Verified",
  PLAUSIBLE: "Plausible",
  UNVERIFIABLE: "Unverifiable",
  DOI_MISMATCH: "DOI mismatch",
  FABRICATED: "Fabricated",
};

const FAITHFULNESS_LABEL: Record<FaithfulnessVerdict, string> = {
  VERIFIED: "Verified",
  MINOR_DISTORTION: "Minor distortion",
  MAJOR_DISTORTION: "Major distortion",
  UNSUPPORTED: "Unsupported",
  ACCESS_LIMITED: "Access limited",
};

export default async function LiteraturePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const persona = getPersona(id);
  if (!persona) notFound();
  const pack = await loadEvidencePack(id);
  const stats = citationStats(pack);
  const entries = uniqueCitations(pack).sort((a, b) => {
    // Verified first
    const verA =
      a.citation.existence === "VERIFIED" &&
      a.citation.faithfulness === "VERIFIED";
    const verB =
      b.citation.existence === "VERIFIED" &&
      b.citation.faithfulness === "VERIFIED";
    if (verA !== verB) return verA ? -1 : 1;
    return a.citation.id.localeCompare(b.citation.id);
  });

  return (
    <div className="mx-auto max-w-7xl px-6 pb-24 pt-12">
      <SectionHeader
        eyebrow={`${persona.displayName} · ${entries.length} unique sources`}
        title="Citation / Index"
        subtitle="Every reference behind this plan, deduped and graded against a two-layer existence + faithfulness gate."
      />

      <div className="mb-10 grid grid-cols-1 gap-4 md:grid-cols-3">
        <GlassCard innerClassName="p-5">
          <ScoreCluster
            stats={[
              {
                label: "Total citations",
                value: stats.total,
                hint: `${entries.length} unique`,
              },
            ]}
          />
        </GlassCard>
        <GlassCard innerClassName="p-5">
          <ScoreCluster
            stats={[
              {
                label: "Citation integrity",
                value: formatPercent(stats.integrity, 0),
                hint: `${stats.fullyVerified} fully verified`,
              },
            ]}
          />
        </GlassCard>
        <GlassCard innerClassName="p-5">
          <ScoreCluster
            stats={[
              {
                label: "Verified existence",
                value: `${stats.verifiedExistence} / ${stats.total}`,
                hint: `${stats.verifiedFaithfulness} faithfulness-verified`,
              },
            ]}
          />
        </GlassCard>
      </div>

      <GlassCard innerClassName="overflow-hidden">
        <div className="hidden grid-cols-[1fr_2fr_120px_120px_56px] gap-4 border-b border-white/[0.05] px-6 py-3 text-[0.6rem] font-semibold uppercase tracking-[0.18em] text-zinc-500 md:grid">
          <span>Identifier / Refs</span>
          <span>Cited claim</span>
          <span>Existence</span>
          <span>Faithfulness</span>
          <span className="text-right">Open</span>
        </div>
        <ul className="divide-y divide-white/[0.05]">
          {entries.map(({ citation, referencedBy }) => {
            const kind = citationKind(citation.id);
            return (
              <li
                key={citation.id}
                className="grid grid-cols-1 gap-3 px-6 py-4 transition-colors hover:bg-white/[0.02] md:grid-cols-[1fr_2fr_120px_120px_56px] md:items-start md:gap-4"
              >
                <div className="flex flex-col gap-1.5">
                  <span className="font-mono text-[0.7rem] text-white">
                    <span className="text-[0.55rem] uppercase tracking-wider text-zinc-500 mr-1.5">
                      {kind}
                    </span>
                    {citation.id}
                  </span>
                  <div className="flex flex-wrap gap-1">
                    {referencedBy.slice(0, 3).map((aid) => (
                      <span
                        key={aid}
                        className="rounded border border-white/[0.08] bg-white/[0.02] px-1.5 py-0.5 font-mono text-[0.55rem] text-zinc-400"
                      >
                        {aid}
                      </span>
                    ))}
                    {referencedBy.length > 3 ? (
                      <span className="self-center text-[0.55rem] text-zinc-500">
                        +{referencedBy.length - 3}
                      </span>
                    ) : null}
                  </div>
                </div>

                <div className="flex flex-col gap-1">
                  {citation.cited_title ? (
                    <p className="text-xs text-white">
                      {citation.cited_title}
                    </p>
                  ) : null}
                  <p className="text-[0.7rem] italic leading-relaxed text-zinc-400">
                    “{truncate(citation.locator_quote, 220)}”
                  </p>
                </div>

                <Verdict
                  dot={EXISTENCE_DOT[citation.existence]}
                  label={EXISTENCE_LABEL[citation.existence]}
                />
                <Verdict
                  dot={FAITHFULNESS_DOT[citation.faithfulness]}
                  label={FAITHFULNESS_LABEL[citation.faithfulness]}
                />

                <div className="md:text-right">
                  <a
                    href={citationHref(citation.id)}
                    target="_blank"
                    rel="noreferrer"
                    aria-label={`Open ${citation.id}`}
                    className="inline-grid h-7 w-7 place-items-center rounded-md border border-white/[0.06] bg-white/[0.02] text-zinc-400 transition-colors hover:border-white/20 hover:text-white"
                  >
                    <ExternalLink className="h-3 w-3" strokeWidth={1.5} />
                  </a>
                </div>
              </li>
            );
          })}
        </ul>
      </GlassCard>
    </div>
  );
}

function Verdict({ dot, label }: { dot: string; label: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className={cn("inline-block h-1.5 w-1.5 rounded-full", dot)} />
      <span className="text-[0.7rem] text-zinc-300">{label}</span>
    </div>
  );
}
