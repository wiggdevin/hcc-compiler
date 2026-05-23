"use client";

import { useState } from "react";
import { AlertTriangle, ChevronDown } from "lucide-react";
import type { PreemptiveHit } from "@/lib/data/types";
import { GlassCard } from "./glass-card";
import { cn } from "@/lib/utils";

interface Props {
  hits: PreemptiveHit[];
}

export function SafetyBanner({ hits }: Props) {
  const [open, setOpen] = useState(true);

  if (hits.length === 0) {
    return (
      <GlassCard innerClassName="px-5 py-4 flex items-center gap-3">
        <div className="grid h-7 w-7 place-items-center rounded-full bg-emerald-500/10 text-emerald-300">
          <AlertTriangle className="h-3.5 w-3.5" strokeWidth={1.5} />
        </div>
        <div className="flex-1">
          <p className="text-sm font-medium text-white">Safety preflight clear</p>
          <p className="text-[0.7rem] text-zinc-500">
            No library-wide contraindication matches against this intake.
          </p>
        </div>
      </GlassCard>
    );
  }

  return (
    <GlassCard innerClassName="overflow-hidden">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        className="flex w-full items-center gap-3 px-5 py-4 text-left transition-colors hover:bg-white/[0.03]"
      >
        <div className="grid h-7 w-7 place-items-center rounded-full bg-amber-500/10 text-amber-300">
          <AlertTriangle className="h-3.5 w-3.5" strokeWidth={1.75} />
        </div>
        <div className="flex-1">
          <p className="text-sm font-medium text-white">
            Safety preflight · {hits.length} hit{hits.length === 1 ? "" : "s"}
          </p>
          <p className="text-[0.7rem] text-zinc-500">
            Library-wide contraindication scan against this intake.
          </p>
        </div>
        <ChevronDown
          className={cn(
            "h-4 w-4 text-zinc-500 transition-transform",
            open && "rotate-180",
          )}
        />
      </button>

      {open ? (
        <ul className="border-t border-white/[0.05] divide-y divide-white/[0.04]">
          {hits.map((hit, i) => (
            <li
              key={`${hit.record_id}-${i}`}
              className="flex flex-col gap-1 px-5 py-3 transition-colors hover:bg-white/[0.025]"
            >
              <div className="flex items-center gap-2">
                <span className="rounded border border-white/10 bg-white/[0.04] px-1.5 py-0.5 font-mono text-[0.6rem] text-zinc-300">
                  {hit.record_id}
                </span>
                <span className="text-[0.6rem] uppercase tracking-[0.16em] text-zinc-500">
                  {hit.record_type}
                </span>
                <span className="ml-auto text-[0.65rem] text-amber-300/80">
                  matches: {hit.matched_needle}
                </span>
              </div>
              <p className="text-xs leading-relaxed text-zinc-300">
                {hit.claim_or_summary}
              </p>
            </li>
          ))}
        </ul>
      ) : null}
    </GlassCard>
  );
}
