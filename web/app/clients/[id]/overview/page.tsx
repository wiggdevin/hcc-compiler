import { Download, ShieldCheck, AlertTriangle } from "lucide-react";
import { loadPackForView } from "@/lib/data/pack-loader";
import {
  domainConfidences,
  overallConfidence,
} from "@/lib/scoring";
import { DOMAIN_META, DOMAIN_ORDER } from "@/lib/data/domains";
import { GlassCard } from "@/components/glass-card";
import { SectionHeader } from "@/components/section-header";
import { ScoreRing } from "@/components/score-ring";
import { SafetyBanner } from "@/components/safety-banner";
import { PrescriptionSection } from "@/components/prescription-section";
import { ScoreExplainer } from "@/components/score-explainer";
import { PrintButton } from "@/components/print-button";
import { SendToClientButton } from "@/components/send-to-client-button";
import { formatDate, formatPercent } from "@/lib/format";

function capitalize(s: string): string {
  if (!s) return s;
  return s.charAt(0).toUpperCase() + s.slice(1);
}

function formatGoalChip(g: string): string {
  return g.replace(/_/g, " ");
}

export default async function OverviewPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const { persona, pack, intake, source } = await loadPackForView(id);

  const overall = overallConfidence(pack);
  const perDomain = domainConfidences(pack);
  const safetyHits = pack.compile_metadata.preemptive_contraindications;

  const totalAtoms = perDomain.reduce((n, d) => n + d.atomCount, 0);
  const totalPatterns = perDomain.reduce((n, d) => n + d.patternCount, 0);

  // Prescription order: only domains with content, sorted by confidence DESC.
  const prescriptionRows = DOMAIN_ORDER
    .map((d) => {
      const row = perDomain.find((p) => p.domain === d)!;
      const block = pack.domain_recommendations[d];
      return { domain: d, row, block };
    })
    .filter(
      ({ block }) => block.atoms.length > 0 || block.patterns.length > 0,
    )
    .sort((a, b) => b.row.confidence - a.row.confidence);

  return (
    <div className="mx-auto max-w-7xl px-6 pb-24 pt-12">
      <SectionHeader
        eyebrow={`${persona.displayName} · compiled ${formatDate(pack.compiled_at)}`}
        title="Plan / Confidence"
        subtitle="Coach-grade prescription stack, sorted by confidence. Library-wide safety preflight surfaces top-right."
      />

      {/* HERO */}
      <section className="grid grid-cols-1 items-stretch gap-6 lg:grid-cols-12">
        {/* LEFT — Goals + status + constraints */}
        <div className="lg:col-span-3">
          <GlassCard innerClassName="flex h-full flex-col gap-4 p-5">
            <p className="text-[0.6rem] font-semibold uppercase tracking-[0.22em] text-zinc-500">
              Goals
            </p>
            <div className="flex flex-wrap gap-1.5">
              {intake.goals.length === 0 ? (
                <span className="text-[0.75rem] text-zinc-500">
                  No goals declared
                </span>
              ) : (
                intake.goals.map((g) => (
                  <span
                    key={g}
                    className="rounded-md border border-white/10 bg-white/[0.04] px-2 py-0.5 text-[0.65rem] font-medium text-zinc-200"
                  >
                    {formatGoalChip(g)}
                  </span>
                ))
              )}
            </div>
            <div className="mt-2 flex flex-col gap-1">
              <p className="text-[0.6rem] font-semibold uppercase tracking-[0.22em] text-zinc-500">
                Training status
              </p>
              <p className="text-sm font-medium text-white">
                {capitalize(intake.training_status)}
              </p>
            </div>
            <div className="flex flex-col gap-1">
              <p className="text-[0.6rem] font-semibold uppercase tracking-[0.22em] text-zinc-500">
                Constraints
              </p>
              {intake.constraints.length === 0 &&
              intake.contraindications.length === 0 ? (
                <p className="text-[0.75rem] text-zinc-500">None on file</p>
              ) : (
                <ul className="flex flex-col gap-0.5">
                  {intake.contraindications.slice(0, 3).map((c, i) => (
                    <li
                      key={`ci-${i}`}
                      className="text-[0.7rem] leading-snug text-zinc-300"
                    >
                      <span className="text-amber-300/80">•</span> {c}
                    </li>
                  ))}
                  {intake.constraints.slice(0, 3).map((c, i) => (
                    <li
                      key={`co-${i}`}
                      className="text-[0.7rem] leading-snug text-zinc-300"
                    >
                      <span className="text-zinc-500">•</span> {c.detail}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          </GlassCard>
        </div>

        {/* CENTER — Ring + Score Explainer */}
        <div className="lg:col-span-6 flex flex-col items-center gap-5 py-2">
          <ScoreRing value={overall} size={200} />
          <p className="text-center text-[0.75rem] text-zinc-400 tabular">
            Plan Confidence {(overall * 100).toFixed(0)}% · {totalAtoms} atom
            {totalAtoms === 1 ? "" : "s"} · {totalPatterns} pattern
            {totalPatterns === 1 ? "" : "s"}
          </p>
          {/* Per-domain confidence pill strip */}
          <div className="flex w-full max-w-md flex-wrap items-center justify-center gap-1.5">
            {perDomain
              .filter((d) => d.atomCount > 0 || d.patternCount > 0)
              .map((d) => {
                const meta = DOMAIN_META[d.domain];
                const Icon = meta.icon;
                return (
                  <span
                    key={d.domain}
                    className="inline-flex items-center gap-1.5 rounded-md border border-white/[0.08] bg-white/[0.025] px-2 py-1 text-[0.65rem] font-medium text-zinc-200"
                  >
                    <Icon
                      className="h-3 w-3 text-zinc-400"
                      strokeWidth={1.5}
                    />
                    <span>{meta.shortLabel}</span>
                    <span className="tabular text-zinc-400">
                      {formatPercent(d.confidence, 0)}
                    </span>
                  </span>
                );
              })}
          </div>
          <div className="w-full max-w-md">
            <ScoreExplainer pack={pack} />
          </div>
        </div>

        {/* RIGHT — Safety summary + meta */}
        <div className="lg:col-span-3">
          <GlassCard innerClassName="flex h-full flex-col gap-4 p-5">
            <div className="flex flex-col gap-1.5">
              <p className="text-[0.6rem] font-semibold uppercase tracking-[0.22em] text-zinc-500">
                Safety preflight
              </p>
              <div className="flex items-center gap-2">
                {safetyHits.length === 0 ? (
                  <ShieldCheck
                    className="h-4 w-4 text-emerald-300"
                    strokeWidth={1.5}
                  />
                ) : (
                  <AlertTriangle
                    className="h-4 w-4 text-amber-300"
                    strokeWidth={1.5}
                  />
                )}
                <span className="text-2xl font-semibold tabular tracking-tight text-white">
                  {safetyHits.length}
                </span>
                <span className="text-[0.65rem] text-zinc-500">
                  {safetyHits.length === 0
                    ? "clear"
                    : safetyHits.length === 1
                    ? "hit"
                    : "hits"}
                </span>
              </div>
              {safetyHits.length > 0 ? (
                <a
                  href="#safety-preflight"
                  className="text-[0.65rem] text-zinc-400 underline-offset-2 hover:text-white hover:underline"
                >
                  View all flags
                </a>
              ) : null}
            </div>
            <div className="h-px bg-white/[0.05]" />
            <div className="flex flex-col gap-1.5">
              <p className="text-[0.6rem] font-semibold uppercase tracking-[0.22em] text-zinc-500">
                Library
              </p>
              <p className="text-sm font-medium text-white tabular">
                v{pack.library_version}
              </p>
            </div>
            <div className="flex flex-col gap-1.5">
              <p className="text-[0.6rem] font-semibold uppercase tracking-[0.22em] text-zinc-500">
                Compiled
              </p>
              <p className="text-[0.7rem] leading-snug text-zinc-300">
                {formatDate(pack.compiled_at)}
              </p>
            </div>
          </GlassCard>
        </div>
      </section>

      {/* PRESCRIPTIONS */}
      <div className="mx-auto mt-16 flex max-w-[1100px] flex-col gap-8 stagger">
        {prescriptionRows.map(({ domain, row, block }) => (
          <PrescriptionSection
            key={domain}
            domain={domain}
            block={block}
            confidence={row.confidence}
            personaSlug={persona.slug}
          />
        ))}
      </div>

      {/* FULL SAFETY BANNER — anchored so the hero "View all flags" link lands here */}
      <div id="safety-preflight" className="mx-auto mt-16 max-w-[1100px]">
        <SafetyBanner hits={safetyHits} />
      </div>

      {/* EXPORT */}
      <div className="no-print mx-auto mt-16 flex max-w-[1100px] flex-wrap items-center justify-between gap-4">
        <a
          href={`/api/export/${persona.slug}/markdown`}
          download
          className="inline-flex items-center gap-2 rounded-md border border-white/10 bg-white/[0.025] px-3.5 py-2 text-[0.75rem] font-medium text-zinc-200 transition-colors hover:border-white/20 hover:bg-white/[0.05] hover:text-white"
        >
          <Download className="h-3.5 w-3.5" strokeWidth={1.5} />
          Download as Markdown
        </a>
        <div className="flex items-center gap-3">
          {source === "coach" ? (
            <SendToClientButton packId={id} clientLabel={persona.displayName} />
          ) : null}
          <PrintButton>Print plan</PrintButton>
        </div>
      </div>
    </div>
  );
}
