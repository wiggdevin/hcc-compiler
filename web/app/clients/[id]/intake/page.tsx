import {
  IdCard,
  ClipboardList,
  ShieldAlert,
  AlertTriangle,
  Activity,
} from "lucide-react";
import { loadPackForView } from "@/lib/data/pack-loader";
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

export default async function IntakePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  const { persona, intake, pack } = await loadPackForView(id);

  const goalLabels = intake.goals.map((g) => g.replace(/_/g, " "));
  const calibration = intake.metabolic_calibration ?? null;
  const safetyHits = pack.compile_metadata.preemptive_contraindications;

  return (
    <div className="mx-auto max-w-7xl px-6 pb-24 pt-12">
      <SectionHeader
        eyebrow="Captured intake"
        title="Client / Status"
        subtitle="Anthropometric, behavioral, and clinical signal — the substrate every recommendation in this plan is conditioned on."
      />

      <div className="stagger grid grid-cols-1 gap-6 lg:grid-cols-12">
        {/* LEFT (8) — Anthropometrics + Diagnostics stacked */}
        <div className="flex flex-col gap-6 lg:col-span-8">
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
        </div>

        {/* RIGHT (4) — downsized Identity + Regimen + Safety preflight */}
        <div className="flex flex-col gap-6 lg:col-span-4">
          <GlassCard emphasis innerClassName="overflow-hidden">
            <div className="flex flex-col gap-3 p-5">
              <div className="flex items-center gap-3">
                <GradientAvatar
                  initials={persona.initials}
                  size={56}
                  className="border-white/20"
                />
                <div className="flex flex-col gap-0.5">
                  <p className="text-[0.6rem] font-semibold uppercase tracking-[0.22em] text-zinc-500">
                    Client
                  </p>
                  <h2 className="text-xl font-semibold tracking-tight text-white">
                    {persona.displayName}
                  </h2>
                </div>
              </div>

              <div className="flex flex-col gap-1.5 border-t border-white/[0.05] pt-3">
                <p className="text-[0.6rem] font-semibold uppercase tracking-[0.22em] text-zinc-500">
                  Training status
                </p>
                <p className="text-sm font-medium capitalize text-white">
                  {intake.training_status}
                </p>
              </div>

              <div className="flex flex-col gap-1.5">
                <p className="text-[0.6rem] font-semibold uppercase tracking-[0.22em] text-zinc-500">
                  Goals
                </p>
                <p className="text-sm capitalize text-zinc-200">
                  {goalLabels.length === 0 ? "—" : goalLabels.join(", ")}
                </p>
              </div>
            </div>
          </GlassCard>

          {intake.current_regimen ? (
            <GlassCard innerClassName="p-5">
              <div className="flex flex-col gap-2">
                <div className="flex items-center gap-2 text-[0.6rem] font-semibold uppercase tracking-[0.22em] text-zinc-500">
                  <Activity className="h-3 w-3" strokeWidth={1.5} />
                  Current regimen
                </div>
                <p className="whitespace-pre-line text-sm leading-relaxed text-zinc-300">
                  {intake.current_regimen}
                </p>
              </div>
            </GlassCard>
          ) : null}

          <GlassCard
            innerClassName={
              safetyHits.length > 0
                ? "p-5 border border-amber-400/15"
                : "p-5"
            }
          >
            <div className="flex flex-col gap-2">
              <div className="flex items-center gap-2 text-[0.6rem] font-semibold uppercase tracking-[0.22em] text-zinc-500">
                {safetyHits.length > 0 ? (
                  <AlertTriangle
                    className="h-3 w-3 text-amber-300"
                    strokeWidth={1.5}
                  />
                ) : (
                  <ShieldAlert className="h-3 w-3" strokeWidth={1.5} />
                )}
                Safety preflight
              </div>
              {safetyHits.length === 0 ? (
                <p className="text-[0.75rem] text-zinc-400">
                  No library-wide contraindications matched this intake.
                </p>
              ) : (
                <>
                  <p className="text-sm font-medium text-amber-50">
                    {safetyHits.length} hit
                    {safetyHits.length === 1 ? "" : "s"}
                  </p>
                  <p className="text-[0.7rem] leading-relaxed text-zinc-400">
                    Library-wide contraindication scan against this intake.
                    Review on the{" "}
                    <a
                      href={`/clients/${persona.slug}/overview`}
                      className="text-white underline-offset-2 hover:underline"
                    >
                      Overview
                    </a>
                    .
                  </p>
                </>
              )}
            </div>
          </GlassCard>
        </div>
      </div>
    </div>
  );
}
