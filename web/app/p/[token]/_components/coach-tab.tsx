"use client";

import { MessageCircle } from "lucide-react";
import type { CoachBrand } from "@/lib/data/share-loader";
import type { Schedule } from "@/lib/schedule/types";

function initialsOf(name: string): string {
  return name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((p) => p[0]?.toUpperCase() ?? "")
    .join("");
}

export function CoachTab({
  coach,
  schedule,
}: {
  coach: CoachBrand;
  schedule: Schedule;
}) {
  const showImage =
    coach.headshot_url && /^https?:\/\//.test(coach.headshot_url);
  const initials = initialsOf(coach.display_name);
  const firstName = coach.display_name.split(/\s+/)[0] ?? coach.display_name;

  const supplementsCount = schedule.supplements.length;

  return (
    <section className="px-5 pb-32 pt-2">
      <p className="text-xs font-medium uppercase tracking-[0.2em] text-emerald-300/70">
        Your coach
      </p>
      <h1 className="mt-2 text-2xl font-light tracking-tight">
        Questions? Talk to {firstName}.
      </h1>

      <div className="mt-7 rounded-2xl border border-white/10 bg-gradient-to-br from-white/[0.04] to-white/[0.01] p-6 backdrop-blur-sm">
        <div className="flex items-center gap-4">
          <div className="relative h-16 w-16 shrink-0 overflow-hidden rounded-full border border-white/10 bg-gradient-to-br from-emerald-500/30 via-cyan-500/20 to-purple-500/20">
            {showImage ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img
                src={coach.headshot_url!}
                alt={coach.display_name}
                className="h-full w-full object-cover"
              />
            ) : (
              <span className="absolute inset-0 grid place-items-center text-base font-semibold text-white/80">
                {initials || "?"}
              </span>
            )}
          </div>
          <div className="min-w-0">
            <p className="truncate text-base font-semibold text-white">
              {coach.display_name}
            </p>
            {coach.practice_name ? (
              <p className="truncate text-xs text-white/55">
                {coach.practice_name}
              </p>
            ) : null}
          </div>
        </div>

        {coach.contact_url && coach.contact_label ? (
          <a
            href={coach.contact_url}
            className="mt-6 flex w-full items-center justify-center gap-2 rounded-xl border border-emerald-400/40 bg-emerald-500/20 px-4 py-3 text-sm font-semibold text-emerald-100 transition hover:bg-emerald-500/30"
          >
            <MessageCircle className="h-4 w-4" />
            {coach.contact_label}
          </a>
        ) : (
          <p className="mt-6 text-xs text-white/40">
            {firstName} hasn&apos;t added a contact method yet. Reply to the
            email you received for the plan.
          </p>
        )}
      </div>

      {supplementsCount > 0 ? (
        <div className="mt-6 rounded-2xl border border-white/10 bg-white/[0.02] p-5">
          <p className="text-xs font-medium uppercase tracking-wider text-white/40">
            Supplements your coach recommends
          </p>
          <ul className="mt-3 space-y-3">
            {schedule.supplements.map((s, i) => (
              <li key={`${i}-${s.name}`}>
                <p className="text-sm font-medium text-white">
                  {s.name} <span className="text-white/50">· {s.dose}</span>
                </p>
                <p className="mt-0.5 text-xs text-white/55">
                  <span className="text-white/40">{s.timing}</span> · {s.why_plain}
                </p>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </section>
  );
}
