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
import type { Citation } from "@/lib/data/types";
import { cn } from "@/lib/utils";

type VerificationVerdict = "verified" | "partial" | "plausible" | "unverifiable";

interface VerificationMeta {
  label: string;
  className: string;
}

const VERIFICATION_STYLES: Record<VerificationVerdict, VerificationMeta> = {
  verified: {
    label: "✓ Verified",
    className:
      "border-emerald-400/30 bg-emerald-400/[0.08] text-emerald-200",
  },
  partial: {
    label: "◐ Partially verified",
    className: "border-amber-300/30 bg-amber-300/[0.08] text-amber-100",
  },
  plausible: {
    label: "◐ Plausible",
    className: "border-amber-300/30 bg-amber-300/[0.06] text-amber-100",
  },
  unverifiable: {
    label: "✗ Unverifiable",
    className: "border-rose-400/30 bg-rose-400/[0.08] text-rose-100",
  },
};

function verificationOf(citation: Citation): VerificationVerdict {
  const exVerified = citation.existence === "VERIFIED";
  const faVerified = citation.faithfulness === "VERIFIED";
  if (exVerified && faVerified) return "verified";
  if (exVerified || faVerified) return "partial";
  if (citation.existence === "PLAUSIBLE") return "plausible";
  return "unverifiable";
}

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

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {entries.map(({ citation, referencedBy }) => {
          const kind = citationKind(citation.id);
          const verdict = verificationOf(citation);
          const style = VERIFICATION_STYLES[verdict];
          return (
            <GlassCard
              key={citation.id}
              innerClassName="flex flex-col gap-3 p-5"
            >
              <div className="flex items-start justify-between gap-3">
                <span className="font-mono text-xs text-white">
                  <span className="text-[0.55rem] uppercase tracking-wider text-zinc-500 mr-1.5">
                    {kind}
                  </span>
                  {citation.id}
                </span>
                <a
                  href={citationHref(citation.id)}
                  target="_blank"
                  rel="noreferrer"
                  aria-label={`Open ${citation.id}`}
                  className="inline-grid h-7 w-7 shrink-0 place-items-center rounded-md border border-white/[0.06] bg-white/[0.02] text-zinc-400 transition-colors hover:border-white/20 hover:text-white"
                >
                  <ExternalLink className="h-3 w-3" strokeWidth={1.5} />
                </a>
              </div>

              {citation.cited_title ? (
                <p className="line-clamp-2 text-sm font-semibold leading-snug text-white">
                  {citation.cited_title}
                </p>
              ) : null}

              <p className="line-clamp-3 text-[0.7rem] italic leading-relaxed text-zinc-400">
                “{truncate(citation.locator_quote, 240)}”
              </p>

              <div className="mt-auto flex flex-wrap items-center justify-between gap-2 pt-1">
                <span
                  className={cn(
                    "inline-flex items-center rounded-md border px-2 py-0.5 text-[0.65rem] font-medium",
                    style.className,
                  )}
                >
                  {style.label}
                </span>
                {referencedBy.length > 0 ? (
                  <div className="flex flex-wrap items-center gap-1">
                    {referencedBy.slice(0, 2).map((aid) => (
                      <span
                        key={aid}
                        className="rounded border border-white/[0.08] bg-white/[0.02] px-1.5 py-0.5 font-mono text-[0.55rem] text-zinc-400"
                      >
                        {aid}
                      </span>
                    ))}
                    {referencedBy.length > 2 ? (
                      <span className="text-[0.55rem] text-zinc-500">
                        +{referencedBy.length - 2}
                      </span>
                    ) : null}
                  </div>
                ) : null}
              </div>
            </GlassCard>
          );
        })}
      </div>
    </div>
  );
}
