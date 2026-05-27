"use client";

import { useState } from "react";
import { Check, Dumbbell, UtensilsCrossed, Moon } from "lucide-react";
import { cn } from "@/lib/utils";
import type {
  DaySchedule,
  Meal,
  Schedule,
  TrainingBlock,
} from "@/lib/schedule/types";
import { DAY_NAMES } from "@/lib/schedule/types";

function dayOfWeekToday(): (typeof DAY_NAMES)[number] {
  // 0=Sun ... 6=Sat → align to Mon-first array
  const map: Record<number, (typeof DAY_NAMES)[number]> = {
    1: "Mon",
    2: "Tue",
    3: "Wed",
    4: "Thu",
    5: "Fri",
    6: "Sat",
    0: "Sun",
  };
  return map[new Date().getDay()];
}

interface CheckItem {
  id: string;
  icon: typeof Dumbbell;
  label: string;
  detail?: string;
}

function actionsFor(day: DaySchedule): CheckItem[] {
  const items: CheckItem[] = [];
  if (day.training) {
    const t = day.training as TrainingBlock;
    items.push({
      id: `training-${day.day}`,
      icon: Dumbbell,
      label: t.title,
      detail:
        t.items
          .slice(0, 4)
          .map((it) => `${it.name}${it.sets ? ` ${it.sets}×${it.reps ?? ""}`.trim() : ""}`)
          .join(" · "),
    });
  }
  for (const m of day.nutrition.meals.slice(0, 3)) {
    items.push({
      id: `meal-${day.day}-${m.meal}`,
      icon: UtensilsCrossed,
      label: m.meal,
      detail: m.suggestion,
    });
  }
  for (const r of day.recovery.slice(0, 2)) {
    items.push({
      id: `recovery-${day.day}-${r}`,
      icon: Moon,
      label: r,
    });
  }
  return items.slice(0, 6);
}

export function TodayTab({ schedule }: { schedule: Schedule }) {
  const today = dayOfWeekToday();
  const day = schedule.days.find((d) => d.day === today) ?? schedule.days[0];
  const [checked, setChecked] = useState<Set<string>>(new Set());

  function toggle(id: string) {
    setChecked((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  const items = actionsFor(day);

  return (
    <section className="px-5 pb-32 pt-2">
      <p className="text-xs font-medium uppercase tracking-[0.2em] text-emerald-300/70">
        {day.day} · This week
      </p>
      <h1 className="mt-2 text-2xl font-light leading-tight tracking-tight">
        {schedule.weekly_focus}
      </h1>

      <ul className="mt-7 space-y-3">
        {items.map(({ id, icon: Icon, label, detail }) => {
          const isChecked = checked.has(id);
          return (
            <li key={id}>
              <button
                onClick={() => toggle(id)}
                className={cn(
                  "flex w-full items-start gap-3 rounded-2xl border p-4 text-left transition",
                  isChecked
                    ? "border-emerald-400/30 bg-emerald-500/10"
                    : "border-white/10 bg-white/[0.02] hover:border-white/20",
                )}
              >
                <span
                  className={cn(
                    "mt-0.5 grid h-7 w-7 shrink-0 place-items-center rounded-full border",
                    isChecked
                      ? "border-emerald-400/60 bg-emerald-400/30 text-emerald-50"
                      : "border-white/15 bg-transparent text-white/40",
                  )}
                  aria-hidden
                >
                  {isChecked ? (
                    <Check className="h-4 w-4" />
                  ) : (
                    <Icon className="h-4 w-4" />
                  )}
                </span>
                <span className="min-w-0 flex-1">
                  <span
                    className={cn(
                      "block text-sm font-medium",
                      isChecked ? "text-emerald-100" : "text-white",
                    )}
                  >
                    {label}
                  </span>
                  {detail ? (
                    <span className="mt-0.5 block text-xs text-white/55">
                      {detail}
                    </span>
                  ) : null}
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </section>
  );
}
