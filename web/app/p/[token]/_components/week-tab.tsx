"use client";

import { Dumbbell, UtensilsCrossed } from "lucide-react";
import type { Schedule } from "@/lib/schedule/types";

export function WeekTab({ schedule }: { schedule: Schedule }) {
  return (
    <section className="px-5 pb-32 pt-2">
      <p className="text-xs font-medium uppercase tracking-[0.2em] text-emerald-300/70">
        Week at a glance
      </p>
      <h1 className="mt-2 text-2xl font-light tracking-tight">7 days</h1>

      <ul className="mt-6 space-y-3">
        {schedule.days.map((day) => (
          <li
            key={day.day}
            className="rounded-2xl border border-white/10 bg-white/[0.02] p-4"
          >
            <div className="flex items-baseline justify-between">
              <h2 className="text-sm font-semibold uppercase tracking-wider text-emerald-200">
                {day.day}
              </h2>
              {day.training?.duration_min ? (
                <span className="text-[11px] text-white/40">
                  {day.training.duration_min} min
                </span>
              ) : null}
            </div>

            {day.training ? (
              <div className="mt-2 flex items-start gap-2.5">
                <Dumbbell className="mt-0.5 h-4 w-4 shrink-0 text-emerald-300/80" />
                <div className="min-w-0">
                  <p className="text-sm font-medium text-white">
                    {day.training.title}
                  </p>
                  <p className="mt-0.5 text-xs text-white/55">
                    {day.training.items
                      .slice(0, 5)
                      .map((it) =>
                        `${it.name}${it.sets ? ` ${it.sets}×${it.reps ?? ""}`.trim() : ""}`,
                      )
                      .join(" · ")}
                  </p>
                </div>
              </div>
            ) : (
              <p className="mt-2 text-xs text-white/40">Rest day</p>
            )}

            <div className="mt-3 flex items-start gap-2.5 border-t border-white/5 pt-3">
              <UtensilsCrossed className="mt-0.5 h-4 w-4 shrink-0 text-cyan-300/70" />
              <div className="min-w-0">
                <p className="text-xs text-white/40">
                  Protein target:{" "}
                  <span className="text-white/70">
                    {day.nutrition.protein_target_g}g
                  </span>
                </p>
                <ul className="mt-1 space-y-0.5">
                  {day.nutrition.meals.slice(0, 4).map((m, i) => (
                    <li key={`${day.day}-${m.meal}-${i}`} className="text-xs text-white/75">
                      <span className="text-white/45">{m.meal}: </span>
                      {m.suggestion}
                    </li>
                  ))}
                </ul>
              </div>
            </div>

            {day.recovery.length ? (
              <p className="mt-3 border-t border-white/5 pt-3 text-xs text-white/50">
                Recovery: {day.recovery.join(" · ")}
              </p>
            ) : null}
          </li>
        ))}
      </ul>
    </section>
  );
}
