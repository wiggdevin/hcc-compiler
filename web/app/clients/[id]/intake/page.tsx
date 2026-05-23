import { notFound } from "next/navigation";
import {
  IdCard,
  ClipboardList,
  Target,
  AlertTriangle,
  CalendarDays,
  Scale,
} from "lucide-react";
import { getPersona } from "@/lib/data/personas";
import { loadEvidencePack, loadIntake } from "@/lib/data/loader";
import { GlassCard } from "@/components/glass-card";
import { IntakePanel } from "@/components/intake-panel";
import {
  DisplayInput,
  DisplaySlider,
  DisplayToggle,
  DisplayCheckbox,
} from "@/components/display-widgets";
import { GradientAvatar } from "@/components/gradient-avatar";
import { SectionHeader } from "@/components/section-header";
import { StatRow } from "@/components/stat-row";
import { formatDate, formatPercent } from "@/lib/format";

export default async function IntakePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const persona = getPersona(id);
  if (!persona) notFound();

  const [intake, pack] = await Promise.all([
    loadIntake(id),
    loadEvidencePack(id),
  ]);

  const goalLabels = intake.goals.map((g) => g.replace(/_/g, " "));
  const calibration = intake.metabolic_calibration ?? null;

  return (
    <div className="mx-auto max-w-7xl px-6 pb-24 pt-12">
      <SectionHeader
        eyebrow="Captured intake"
        title="Client / Status"
        subtitle="Anthropometric, behavioral, and clinical signal — the substrate every recommendation in this plan is conditioned on."
      />

      <div className="stagger grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* LEFT — Anthropometrics */}
        <div className="lg:col-span-3">
          <IntakePanel icon={IdCard} title="Anthropometrics">
            <DisplayInput label="Client ID" value={intake.client_id} />
            <div className="grid grid-cols-2 gap-3">
              <DisplayInput
                label="Height (cm)"
                value={intake.demographics.height_cm.toFixed(0)}
              />
              <DisplayInput
                label="Weight (kg)"
                value={intake.demographics.weight_kg.toFixed(1)}
              />
            </div>
            <div className="grid grid-cols-2 gap-3">
              <DisplayInput label="Age" value={intake.demographics.age} />
              <DisplayInput label="Sex" value={intake.demographics.sex} />
            </div>

            {calibration !== null ? (
              <>
                <DisplaySlider
                  label="Metabolic calibration"
                  value={calibration}
                  min={0.5}
                  max={1.5}
                  format={(v) => `${(v * 100).toFixed(0)}%`}
                />
                <DisplayToggle
                  label="Calibration applied to TDEE"
                  on={true}
                />
              </>
            ) : (
              <DisplayToggle label="Metabolic calibration applied" on={false} />
            )}
          </IntakePanel>
        </div>

        {/* CENTER — Identity card */}
        <div className="lg:col-span-6">
          <GlassCard emphasis innerClassName="overflow-hidden">
            <div className="flex flex-col gap-8 p-8 lg:p-10">
              <div className="flex items-center gap-5">
                <GradientAvatar
                  initials={persona.initials}
                  size={72}
                  className="border-white/20"
                />
                <div className="flex flex-col gap-1">
                  <p className="text-[0.65rem] font-semibold uppercase tracking-[0.22em] text-zinc-500">
                    Client
                  </p>
                  <h2 className="text-3xl font-semibold tracking-tight text-white">
                    {persona.displayName}
                  </h2>
                  <p className="text-xs text-zinc-400">{persona.tagline}</p>
                </div>
              </div>

              <div className="grid grid-cols-2 gap-x-8 gap-y-1">
                <StatRow
                  label="Training status"
                  value={
                    <span className="capitalize">{intake.training_status}</span>
                  }
                />
                <StatRow
                  label="Goals"
                  value={
                    <span className="capitalize">{goalLabels.join(", ")}</span>
                  }
                />
                <StatRow
                  label="Constraints"
                  value={
                    intake.constraints.length === 0
                      ? "—"
                      : intake.constraints.length
                  }
                />
                <StatRow
                  label="Contraindications"
                  value={
                    intake.contraindications.length === 0
                      ? "—"
                      : intake.contraindications.length
                  }
                />
              </div>

              {intake.current_regimen ? (
                <div className="space-y-2">
                  <p className="text-[0.65rem] font-semibold uppercase tracking-[0.22em] text-zinc-500">
                    Current regimen
                  </p>
                  <p className="whitespace-pre-line text-sm leading-relaxed text-zinc-300">
                    {intake.current_regimen}
                  </p>
                </div>
              ) : null}

              <div className="flex items-center justify-between border-t border-white/[0.06] pt-5">
                <div className="flex items-center gap-2 text-[0.65rem] font-medium uppercase tracking-[0.18em] text-zinc-500">
                  <CalendarDays className="h-3 w-3" strokeWidth={1.5} />
                  Compiled {formatDate(pack.compiled_at)}
                </div>
                <div className="flex items-center gap-2 text-[0.65rem] font-medium uppercase tracking-[0.18em] text-zinc-500">
                  <Scale className="h-3 w-3" strokeWidth={1.5} />
                  Library v{pack.library_version}
                </div>
              </div>
            </div>
          </GlassCard>
        </div>

        {/* RIGHT — Diagnostics */}
        <div className="lg:col-span-3">
          <IntakePanel icon={ClipboardList} title="Diagnostics">
            {intake.contraindications.length === 0 &&
            intake.constraints.length === 0 ? (
              <p className="text-xs text-zinc-500">
                No clinical contraindications or constraints reported.
              </p>
            ) : (
              <>
                {intake.contraindications.length > 0 ? (
                  <div className="space-y-1.5">
                    <p className="px-1 text-[0.6rem] font-semibold uppercase tracking-[0.18em] text-zinc-500">
                      Contraindications
                    </p>
                    {intake.contraindications.map((c, i) => (
                      <DisplayCheckbox key={i} label={c} />
                    ))}
                  </div>
                ) : null}

                {intake.constraints.length > 0 ? (
                  <div className="space-y-1.5">
                    <p className="px-1 text-[0.6rem] font-semibold uppercase tracking-[0.18em] text-zinc-500">
                      Constraints
                    </p>
                    {intake.constraints.map((c, i) => (
                      <DisplayCheckbox
                        key={i}
                        label={c.type}
                        detail={c.detail}
                      />
                    ))}
                  </div>
                ) : null}
              </>
            )}
          </IntakePanel>

          {pack.compile_metadata.preemptive_contraindications.length > 0 ? (
            <div className="mt-6">
              <GlassCard innerClassName="p-5">
                <div className="flex items-center gap-2 text-xs text-amber-200/80">
                  <AlertTriangle className="h-3.5 w-3.5" strokeWidth={1.5} />
                  <span className="font-medium">
                    {
                      pack.compile_metadata.preemptive_contraindications
                        .length
                    }{" "}
                    safety preflight hit
                    {pack.compile_metadata.preemptive_contraindications
                      .length === 1
                      ? ""
                      : "s"}
                  </span>
                </div>
                <p className="mt-2 text-[0.7rem] leading-relaxed text-zinc-400">
                  Library-wide contraindication scan against this intake.
                  Review them on the{" "}
                  <a
                    href={`/clients/${persona.slug}/overview`}
                    className="text-white underline-offset-2 hover:underline"
                  >
                    Overview
                  </a>
                  .
                </p>
              </GlassCard>
            </div>
          ) : null}
        </div>
      </div>
    </div>
  );
}
