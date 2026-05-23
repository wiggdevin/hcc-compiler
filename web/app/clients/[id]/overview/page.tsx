import { notFound } from "next/navigation";
import { ShieldCheck, BookOpen, Activity, AlertOctagon } from "lucide-react";
import { getPersona } from "@/lib/data/personas";
import { loadEvidencePack } from "@/lib/data/loader";
import {
  domainConfidences,
  overallConfidence,
  citationStats,
} from "@/lib/scoring";
import { DOMAIN_META, DOMAIN_ORDER } from "@/lib/data/domains";
import { GlassCard } from "@/components/glass-card";
import { SectionHeader } from "@/components/section-header";
import { ScoreRing } from "@/components/score-ring";
import { ScoreTag } from "@/components/score-tag";
import { ScoreCluster } from "@/components/score-cluster";
import { SafetyBanner } from "@/components/safety-banner";
import { DomainTile } from "@/components/domain-tile";
import { formatPercent, formatDate } from "@/lib/format";

const TAG_POSITIONS: Record<
  string,
  { className: string; side: "left" | "right" }
> = {
  // Three tags on each side of the ring, vertically distributed.
  nutrition:    { className: "top-[8%]  right-full mr-[-1rem] -translate-x-1",          side: "left" },
  training:     { className: "top-[8%]  left-full  ml-[-1rem]  translate-x-1",          side: "right" },
  recovery:     { className: "top-[44%] right-full mr-[-1.5rem] -translate-x-2",        side: "left" },
  conditioning: { className: "top-[44%] left-full  ml-[-1.5rem] translate-x-2",         side: "right" },
  supplements:  { className: "bottom-[8%] right-full mr-[-1rem] -translate-x-1",        side: "left" },
  behavioral:   { className: "bottom-[8%] left-full  ml-[-1rem] translate-x-1",         side: "right" },
};

export default async function OverviewPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const persona = getPersona(id);
  if (!persona) notFound();
  const pack = await loadEvidencePack(id);

  const overall = overallConfidence(pack);
  const perDomain = domainConfidences(pack);
  const cits = citationStats(pack);
  const safetyHits = pack.compile_metadata.preemptive_contraindications;

  const totalAtoms = perDomain.reduce((n, d) => n + d.atomCount, 0);
  const totalPatterns = perDomain.reduce((n, d) => n + d.patternCount, 0);

  return (
    <div className="mx-auto max-w-7xl px-6 pb-24 pt-12">
      <SectionHeader
        eyebrow={`${persona.displayName} · compiled ${formatDate(pack.compiled_at)}`}
        title="Plan / Confidence"
        subtitle="Aggregate signal across all six prescription domains, with library-wide safety preflight."
      />

      {/* HERO */}
      <section className="relative grid grid-cols-1 items-center gap-10 lg:grid-cols-12">
        {/* LEFT rail */}
        <div className="lg:col-span-3">
          <ScoreCluster
            stats={[
              {
                label: "Plan atoms",
                value: totalAtoms,
                hint: `${totalPatterns} patterns indexed`,
              },
              {
                label: "Citation integrity",
                value: formatPercent(cits.integrity, 0),
                hint: `${cits.fullyVerified} of ${cits.total} verified`,
              },
              {
                label: "Domains scored",
                value: perDomain.filter((d) => d.atomCount > 0).length,
                hint: "of 6",
              },
            ]}
          />
        </div>

        {/* CENTER ring */}
        <div className="lg:col-span-6 flex items-center justify-center py-12">
          <div className="relative">
            <ScoreRing value={overall} size={320} />
            {/* Floating biometric tags — one per domain */}
            {DOMAIN_ORDER.map((d) => {
              const row = perDomain.find((p) => p.domain === d);
              const pos = TAG_POSITIONS[d];
              if (!row || !pos) return null;
              if (row.atomCount === 0 && row.patternCount === 0) return null;
              const meta = DOMAIN_META[d];
              return (
                <ScoreTag
                  key={d}
                  icon={meta.icon}
                  label={meta.shortLabel}
                  value={row.confidence}
                  side={pos.side}
                  className={pos.className}
                />
              );
            })}
          </div>
        </div>

        {/* RIGHT rail */}
        <div className="lg:col-span-3">
          <ScoreCluster
            align="right"
            stats={[
              {
                label: "Safety preflight",
                value: safetyHits.length,
                hint:
                  safetyHits.length === 0
                    ? "no library matches"
                    : `${safetyHits.length} contraindication match${safetyHits.length === 1 ? "" : "es"}`,
              },
              {
                label: "Highest confidence",
                value:
                  formatPercent(
                    Math.max(...perDomain.map((p) => p.confidence)),
                    0,
                  ),
                hint:
                  DOMAIN_META[
                    [...perDomain].sort((a, b) =>
                      b.confidence - a.confidence,
                    )[0].domain
                  ].label,
              },
              {
                label: "Library",
                value: `v${pack.library_version}`,
                hint: `${persona.displayName.toLowerCase()}.json`,
              },
            ]}
          />
        </div>
      </section>

      {/* SAFETY BANNER */}
      <div className="mt-16">
        <SafetyBanner hits={safetyHits} />
      </div>

      {/* DOMAIN TILES */}
      <div className="mt-16">
        <div className="mb-6 flex items-center gap-3">
          <Activity className="h-4 w-4 text-zinc-500" strokeWidth={1.5} />
          <h2 className="text-xs font-semibold uppercase tracking-[0.22em] text-zinc-400">
            Domain breakdown
          </h2>
        </div>
        <div className="stagger grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {DOMAIN_ORDER.map((d) => {
            const row = perDomain.find((p) => p.domain === d)!;
            const block = pack.domain_recommendations[d];
            const topClaim =
              block.patterns[0]?.applies_because ??
              block.atoms[0]?.claim ??
              undefined;
            return (
              <DomainTile
                key={d}
                domain={d}
                confidence={row.confidence}
                atomCount={row.atomCount}
                patternCount={row.patternCount}
                topClaim={topClaim}
                personaSlug={persona.slug}
              />
            );
          })}
        </div>
      </div>

      {/* SECONDARY STATS ROW */}
      <div className="stagger mt-16 grid grid-cols-1 gap-4 md:grid-cols-3">
        <GlassCard innerClassName="flex items-center gap-4 p-5">
          <div className="grid h-10 w-10 place-items-center rounded-full border border-white/10 bg-white/[0.03]">
            <ShieldCheck className="h-4 w-4 text-white" strokeWidth={1.5} />
          </div>
          <div className="flex-1">
            <p className="text-[0.65rem] uppercase tracking-[0.18em] text-zinc-500">
              Safety integrity
            </p>
            <p className="text-xl font-semibold text-white tabular">
              {safetyHits.length === 0
                ? "Clean"
                : `${safetyHits.length} flagged`}
            </p>
          </div>
        </GlassCard>
        <GlassCard innerClassName="flex items-center gap-4 p-5">
          <div className="grid h-10 w-10 place-items-center rounded-full border border-white/10 bg-white/[0.03]">
            <BookOpen className="h-4 w-4 text-white" strokeWidth={1.5} />
          </div>
          <div className="flex-1">
            <p className="text-[0.65rem] uppercase tracking-[0.18em] text-zinc-500">
              Citations indexed
            </p>
            <p className="text-xl font-semibold text-white tabular">
              {cits.total}
            </p>
          </div>
        </GlassCard>
        <GlassCard innerClassName="flex items-center gap-4 p-5">
          <div className="grid h-10 w-10 place-items-center rounded-full border border-white/10 bg-white/[0.03]">
            <AlertOctagon className="h-4 w-4 text-white" strokeWidth={1.5} />
          </div>
          <div className="flex-1">
            <p className="text-[0.65rem] uppercase tracking-[0.18em] text-zinc-500">
              Inline contraindications
            </p>
            <p className="text-xl font-semibold text-white tabular">
              {pack.compile_metadata.contraindication_hits.length}
            </p>
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
