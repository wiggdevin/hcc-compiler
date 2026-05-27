"use client";

import { useState } from "react";
import { ChevronDown, ChevronUp, Sparkles } from "lucide-react";
import { cn } from "@/lib/utils";
import type { Schedule } from "@/lib/schedule/types";

export function WhyTab({ schedule }: { schedule: Schedule }) {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  return (
    <section className="px-5 pb-32 pt-2">
      <p className="text-xs font-medium uppercase tracking-[0.2em] text-emerald-300/70">
        The science
      </p>
      <h1 className="mt-2 text-2xl font-light tracking-tight">
        Why this works
      </h1>
      <p className="mt-2 text-sm text-white/55">
        Every recommendation in your plan is backed by published research. Tap
        any card to see what the science says.
      </p>

      <ul className="mt-6 space-y-3">
        {schedule.recommendations.map((rec, idx) => {
          const isOpen = expandedIdx === idx;
          return (
            <li
              key={`${idx}-${rec.headline}`}
              className={cn(
                "rounded-2xl border bg-white/[0.02] transition",
                isOpen
                  ? "border-emerald-400/30"
                  : "border-white/10 hover:border-white/20",
              )}
            >
              <button
                onClick={() => setExpandedIdx(isOpen ? null : idx)}
                className="flex w-full items-start gap-3 p-4 text-left"
                aria-expanded={isOpen}
              >
                <Sparkles
                  className={cn(
                    "mt-0.5 h-5 w-5 shrink-0",
                    isOpen ? "text-emerald-300" : "text-white/40",
                  )}
                />
                <span className="min-w-0 flex-1">
                  <span className="block text-sm font-medium text-white">
                    {rec.headline}
                  </span>
                  <span className="mt-1 block text-xs text-white/60">
                    {rec.why_plain}
                  </span>
                </span>
                {isOpen ? (
                  <ChevronUp className="h-4 w-4 shrink-0 text-white/40" />
                ) : (
                  <ChevronDown className="h-4 w-4 shrink-0 text-white/40" />
                )}
              </button>

              {isOpen && rec.backing_atom_ids.length > 0 ? (
                <div className="border-t border-white/5 px-4 py-3">
                  <p className="text-[11px] font-medium uppercase tracking-wider text-white/40">
                    Backing evidence
                  </p>
                  <ul className="mt-1.5 flex flex-wrap gap-1.5">
                    {rec.backing_atom_ids.map((id) => (
                      <li
                        key={id}
                        className="rounded-full border border-white/10 bg-white/5 px-2 py-0.5 font-mono text-[10px] text-white/60"
                      >
                        {id}
                      </li>
                    ))}
                  </ul>
                  <p className="mt-2 text-[11px] text-white/35">
                    Each ID points to a peer-reviewed paper in your coach&apos;s
                    library.
                  </p>
                </div>
              ) : null}
            </li>
          );
        })}
      </ul>
    </section>
  );
}
