"use client";

import { useMemo, useState } from "react";
import {
  ALL_GOALS,
  ALL_SEX,
  ALL_TRAINING_STATUS,
  CONSTRAINT_TYPES,
  blankIntake,
  intakeToYaml,
  validateIntake,
  type ClientIntake,
  type Constraint,
  type Goal,
  type Sex,
  type TrainingStatus,
} from "@/lib/intake-yaml";

const sectionClass =
  "rounded-2xl border border-white/10 bg-white/[0.02] p-6 backdrop-blur-sm";
const labelClass = "block text-xs font-medium uppercase tracking-wider text-white/60";
const inputClass =
  "mt-1 w-full rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-sm text-white placeholder-white/30 focus:border-white/30 focus:outline-none";
const buttonClass =
  "inline-flex items-center justify-center rounded-lg border border-white/15 bg-white/[0.06] px-4 py-2 text-sm font-medium text-white transition hover:bg-white/[0.12]";
const primaryButtonClass =
  "inline-flex items-center justify-center rounded-lg border border-emerald-400/40 bg-emerald-500/20 px-5 py-2.5 text-sm font-semibold text-emerald-100 transition hover:bg-emerald-500/30 disabled:cursor-not-allowed disabled:opacity-40";

function Chip({
  label,
  active,
  onClick,
}: {
  label: string;
  active: boolean;
  onClick: () => void;
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      className={
        active
          ? "rounded-full border border-emerald-400/60 bg-emerald-500/20 px-3 py-1 text-xs font-medium text-emerald-100"
          : "rounded-full border border-white/15 bg-white/[0.04] px-3 py-1 text-xs font-medium text-white/70 transition hover:bg-white/[0.10]"
      }
    >
      {label}
    </button>
  );
}

export default function NewClientPage() {
  const [intake, setIntake] = useState<ClientIntake>(blankIntake);
  const [showYaml, setShowYaml] = useState(false);

  const errors = useMemo(() => validateIntake(intake), [intake]);
  const yamlText = useMemo(() => intakeToYaml(intake), [intake]);

  function update<K extends keyof ClientIntake>(key: K, value: ClientIntake[K]) {
    setIntake((prev) => ({ ...prev, [key]: value }));
  }

  function updateDemo<K extends keyof ClientIntake["demographics"]>(
    key: K,
    value: ClientIntake["demographics"][K],
  ) {
    setIntake((prev) => ({
      ...prev,
      demographics: { ...prev.demographics, [key]: value },
    }));
  }

  function toggleGoal(goal: Goal) {
    setIntake((prev) => ({
      ...prev,
      goals: prev.goals.includes(goal)
        ? prev.goals.filter((g) => g !== goal)
        : [...prev.goals, goal],
    }));
  }

  function addConstraint() {
    setIntake((prev) => ({
      ...prev,
      constraints: [...prev.constraints, { type: "injury", detail: "" }],
    }));
  }

  function updateConstraint(idx: number, patch: Partial<Constraint>) {
    setIntake((prev) => ({
      ...prev,
      constraints: prev.constraints.map((c, i) => (i === idx ? { ...c, ...patch } : c)),
    }));
  }

  function removeConstraint(idx: number) {
    setIntake((prev) => ({
      ...prev,
      constraints: prev.constraints.filter((_, i) => i !== idx),
    }));
  }

  function addContraindication() {
    setIntake((prev) => ({ ...prev, contraindications: [...prev.contraindications, ""] }));
  }

  function updateContraindication(idx: number, value: string) {
    setIntake((prev) => ({
      ...prev,
      contraindications: prev.contraindications.map((c, i) => (i === idx ? value : c)),
    }));
  }

  function removeContraindication(idx: number) {
    setIntake((prev) => ({
      ...prev,
      contraindications: prev.contraindications.filter((_, i) => i !== idx),
    }));
  }

  function downloadYaml() {
    const blob = new Blob([yamlText], { type: "text/yaml;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    const filename = (intake.client_id || "intake").replace(/[^a-z0-9_-]/gi, "_");
    a.download = `intake_${filename}.yaml`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  }

  async function copyYaml() {
    try {
      await navigator.clipboard.writeText(yamlText);
    } catch {
      /* ignore — fallback would be a textarea select */
    }
  }

  return (
    <main className="mx-auto w-full max-w-4xl px-4 py-12 md:px-8">
      <header className="mb-10">
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-emerald-300/70">
          New client intake
        </p>
        <h1 className="mt-3 text-3xl font-light tracking-tight text-white md:text-4xl">
          Build a personalized evidence pack
        </h1>
        <p className="mt-3 max-w-2xl text-sm leading-relaxed text-white/60">
          Fill out the client&apos;s profile, goals, and constraints. The form produces a
          schema-valid YAML intake ready for the compiler. No data leaves this page.
        </p>
      </header>

      <div className="space-y-6">
        <section className={sectionClass}>
          <h2 className="text-base font-medium text-white">Identity</h2>
          <div className="mt-4 grid gap-4 md:grid-cols-2">
            <div>
              <label className={labelClass}>Client ID (slug)</label>
              <input
                type="text"
                value={intake.client_id}
                onChange={(e) => update("client_id", e.target.value)}
                placeholder="e.g. jane_doe_2026"
                className={inputClass}
              />
            </div>
            <div>
              <label className={labelClass}>Library version</label>
              <input
                type="text"
                value={intake.library_version}
                onChange={(e) => update("library_version", e.target.value)}
                placeholder="0.1.0"
                className={inputClass}
              />
            </div>
          </div>
        </section>

        <section className={sectionClass}>
          <h2 className="text-base font-medium text-white">Demographics</h2>
          <div className="mt-4 grid gap-4 md:grid-cols-4">
            <div>
              <label className={labelClass}>Age</label>
              <input
                type="number"
                min={14}
                max={100}
                value={intake.demographics.age}
                onChange={(e) => updateDemo("age", parseInt(e.target.value, 10) || 0)}
                className={inputClass}
              />
            </div>
            <div>
              <label className={labelClass}>Sex</label>
              <select
                value={intake.demographics.sex}
                onChange={(e) => updateDemo("sex", e.target.value as Sex)}
                className={inputClass}
              >
                {ALL_SEX.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className={labelClass}>Weight (kg)</label>
              <input
                type="number"
                step={0.1}
                min={0}
                max={300}
                value={intake.demographics.weight_kg}
                onChange={(e) => updateDemo("weight_kg", parseFloat(e.target.value) || 0)}
                className={inputClass}
              />
            </div>
            <div>
              <label className={labelClass}>Height (cm)</label>
              <input
                type="number"
                step={0.1}
                min={0}
                max={250}
                value={intake.demographics.height_cm}
                onChange={(e) => updateDemo("height_cm", parseFloat(e.target.value) || 0)}
                className={inputClass}
              />
            </div>
          </div>
        </section>

        <section className={sectionClass}>
          <h2 className="text-base font-medium text-white">Training status & goals</h2>
          <div className="mt-4">
            <label className={labelClass}>Training status</label>
            <select
              value={intake.training_status}
              onChange={(e) => update("training_status", e.target.value as TrainingStatus)}
              className={inputClass}
            >
              {ALL_TRAINING_STATUS.map((t) => (
                <option key={t} value={t}>
                  {t}
                </option>
              ))}
            </select>
          </div>
          <div className="mt-5">
            <label className={labelClass}>Goals (pick one or more)</label>
            <div className="mt-3 flex flex-wrap gap-2">
              {ALL_GOALS.map((goal) => (
                <Chip
                  key={goal}
                  label={goal.replace("_", " ")}
                  active={intake.goals.includes(goal)}
                  onClick={() => toggleGoal(goal)}
                />
              ))}
            </div>
          </div>
        </section>

        <section className={sectionClass}>
          <h2 className="text-base font-medium text-white">Current regimen</h2>
          <p className="mt-1 text-xs text-white/50">
            Long-form free text. Mention training schedule, nutrition style, supplements, sleep
            patterns, anything coach-relevant. Cycle phase, meal timing windows, etc.
          </p>
          <textarea
            value={intake.current_regimen}
            onChange={(e) => update("current_regimen", e.target.value)}
            rows={6}
            maxLength={2000}
            className={`${inputClass} font-mono`}
            placeholder="Trains 4x/week upper-lower split, ~12 hard sets per muscle. Eats 2300 kcal in a compressed 6-hour window 11am-5pm. NDT for hypothyroidism 7am, supplements creatine 5g/day, omega-3 2g/day…"
          />
          <p className="mt-1 text-right text-xs text-white/40">
            {intake.current_regimen.length}/2000
          </p>
        </section>

        <section className={sectionClass}>
          <div className="flex items-center justify-between">
            <h2 className="text-base font-medium text-white">Constraints</h2>
            <button type="button" onClick={addConstraint} className={buttonClass}>
              + Add constraint
            </button>
          </div>
          <p className="mt-1 text-xs text-white/50">
            Injuries, dietary restrictions, schedule limits, equipment access, etc. The compiler
            uses these to weave constraint-aware notes into the prescription.
          </p>
          <div className="mt-4 space-y-3">
            {intake.constraints.length === 0 && (
              <p className="text-xs italic text-white/40">No constraints recorded.</p>
            )}
            {intake.constraints.map((c, idx) => (
              <div key={idx} className="grid gap-3 md:grid-cols-[8rem_1fr_auto]">
                <select
                  value={c.type}
                  onChange={(e) => updateConstraint(idx, { type: e.target.value })}
                  className={inputClass}
                >
                  {CONSTRAINT_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
                <input
                  type="text"
                  value={c.detail}
                  onChange={(e) => updateConstraint(idx, { detail: e.target.value })}
                  placeholder="e.g. Post-lumbar-spinal-fusion (~4 yr); cleared for lifting"
                  className={inputClass}
                />
                <button
                  type="button"
                  onClick={() => removeConstraint(idx)}
                  className="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-xs text-white/60 hover:bg-white/[0.10]"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        </section>

        <section className={sectionClass}>
          <div className="flex items-center justify-between">
            <h2 className="text-base font-medium text-white">Contraindications</h2>
            <button type="button" onClick={addContraindication} className={buttonClass}>
              + Add contraindication
            </button>
          </div>
          <p className="mt-1 text-xs text-white/50">
            Medical contraindications that flag safety preflight. Examples: &ldquo;CKD stage
            2&rdquo;, &ldquo;MASLD (fatty liver disease)&rdquo;, &ldquo;iron deficiency
            (pending labs)&rdquo;.
          </p>
          <div className="mt-4 space-y-3">
            {intake.contraindications.length === 0 && (
              <p className="text-xs italic text-white/40">No contraindications recorded.</p>
            )}
            {intake.contraindications.map((c, idx) => (
              <div key={idx} className="grid gap-3 md:grid-cols-[1fr_auto]">
                <input
                  type="text"
                  value={c}
                  onChange={(e) => updateContraindication(idx, e.target.value)}
                  placeholder="e.g. CKD stage 2"
                  className={inputClass}
                />
                <button
                  type="button"
                  onClick={() => removeContraindication(idx)}
                  className="rounded-lg border border-white/10 bg-white/[0.04] px-3 py-2 text-xs text-white/60 hover:bg-white/[0.10]"
                >
                  Remove
                </button>
              </div>
            ))}
          </div>
        </section>

        <section className={sectionClass}>
          <h2 className="text-base font-medium text-white">Optional: metabolic calibration</h2>
          <p className="mt-1 text-xs text-white/50">
            Measured maintenance ÷ predicted TDEE. Typical observed range 0.5–1.5. Leave blank if
            unknown; the compiler uses predicted TDEE.
          </p>
          <input
            type="number"
            step={0.01}
            min={0.5}
            max={1.5}
            value={intake.metabolic_calibration ?? ""}
            onChange={(e) =>
              update(
                "metabolic_calibration",
                e.target.value === "" ? null : parseFloat(e.target.value),
              )
            }
            placeholder="e.g. 0.78 (David's measured ~22% metabolic inefficiency)"
            className={`${inputClass} max-w-xs`}
          />
        </section>

        {errors.length > 0 && (
          <div className="rounded-2xl border border-amber-400/30 bg-amber-500/10 p-4 text-sm text-amber-100">
            <p className="font-medium">Resolve before download:</p>
            <ul className="mt-2 list-disc pl-5">
              {errors.map((err) => (
                <li key={err.field}>
                  <span className="font-mono text-xs">{err.field}</span> — {err.message}
                </li>
              ))}
            </ul>
          </div>
        )}

        <div className="flex flex-wrap items-center gap-3">
          <button
            type="button"
            onClick={downloadYaml}
            disabled={errors.length > 0}
            className={primaryButtonClass}
          >
            Download YAML
          </button>
          <button type="button" onClick={copyYaml} className={buttonClass}>
            Copy to clipboard
          </button>
          <button type="button" onClick={() => setShowYaml((v) => !v)} className={buttonClass}>
            {showYaml ? "Hide" : "Preview"} YAML
          </button>
        </div>

        {showYaml && (
          <section className={sectionClass}>
            <h2 className="text-base font-medium text-white">YAML preview</h2>
            <pre className="mt-4 overflow-x-auto rounded-lg bg-black/40 p-4 text-xs leading-relaxed text-emerald-100/90">
              {yamlText}
            </pre>
          </section>
        )}
      </div>

      <footer className="mt-12 border-t border-white/10 pt-6 text-xs text-white/40">
        Schema mirrors <span className="font-mono">src/hcc_compiler/sp2/intake.py</span>. The
        compiler validates strictly at compile time — keep field names exact.
      </footer>
    </main>
  );
}
