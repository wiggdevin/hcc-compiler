import Link from "next/link";
import { ArrowRight } from "lucide-react";
import { DOMAIN_META } from "@/lib/data/domains";
import type { Domain } from "@/lib/data/types";
import { formatPercent } from "@/lib/format";
import { GlassCard } from "./glass-card";

interface Props {
  domain: Domain;
  confidence: number;
  atomCount: number;
  patternCount: number;
  topClaim?: string;
  personaSlug: string;
}

export function DomainTile({
  domain,
  confidence,
  atomCount,
  patternCount,
  topClaim,
  personaSlug,
}: Props) {
  const meta = DOMAIN_META[domain];
  const Icon = meta.icon;
  const href = `/clients/${personaSlug}/${meta.hostRoute}${
    meta.routeHash ? `#${meta.routeHash}` : ""
  }`;
  const isEmpty = atomCount === 0 && patternCount === 0;

  return (
    <Link href={href} className="group block">
      <GlassCard innerClassName="relative h-full p-6 overflow-hidden">
        {/* Accent glow */}
        <div className="pointer-events-none absolute -right-12 -top-12 h-40 w-40 rounded-full bg-blue-500/[0.07] blur-3xl" />

        <div className="relative flex h-full flex-col gap-5">
          <div className="flex items-start justify-between">
            <div className="grid h-10 w-10 place-items-center rounded-full border border-white/10 bg-white/[0.03]">
              <Icon className="h-4 w-4 text-white" strokeWidth={1.5} />
            </div>
            <ArrowRight
              className="h-4 w-4 text-zinc-500 transition-all group-hover:translate-x-1 group-hover:text-white"
              strokeWidth={1.5}
            />
          </div>

          <div className="flex flex-col gap-1">
            <h3 className="text-lg font-semibold tracking-tight text-white">
              {meta.label}
            </h3>
            <p className="text-[0.65rem] uppercase tracking-[0.18em] text-zinc-500">
              {patternCount} pattern{patternCount === 1 ? "" : "s"} ·{" "}
              {atomCount} atom{atomCount === 1 ? "" : "s"}
            </p>
          </div>

          {topClaim ? (
            <p className="line-clamp-3 text-xs leading-relaxed text-zinc-400">
              {topClaim}
            </p>
          ) : isEmpty ? (
            <p className="text-xs text-zinc-600 italic">
              No recommendations for this client.
            </p>
          ) : null}

          <div className="mt-auto flex items-center justify-between border-t border-white/[0.05] pt-4">
            <span className="text-[0.6rem] font-medium uppercase tracking-[0.18em] text-zinc-500">
              Confidence
            </span>
            <span className="text-lg font-semibold tabular text-white">
              {isEmpty ? "—" : formatPercent(confidence, 0)}
            </span>
          </div>
        </div>
      </GlassCard>
    </Link>
  );
}
