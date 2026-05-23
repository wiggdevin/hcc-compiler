import { ChevronRight, ArrowUpRight } from "lucide-react";
import type { AtomMatch, Domain, DomainBlock } from "@/lib/data/types";
import { DOMAIN_META } from "@/lib/data/domains";
import { citationHref, formatPercent, truncate } from "@/lib/format";
import { GlassCard } from "./glass-card";
import { ScorePill } from "./score-pill";
import { PatternCard } from "./pattern-card";
import { AtomCard } from "./atom-card";

interface Props {
  domain: Domain;
  block: DomainBlock;
  confidence: number;
  personaSlug: string;
}

/**
 * One stacked prescription section per domain. Top pattern renders expanded;
 * additional patterns + standalone atoms collapse into <details>. The shape
 * mirrors carl.md's coach-grade prescription so the overview can sell.
 */
export function PrescriptionSection({
  domain,
  block,
  confidence,
  personaSlug,
}: Props) {
  const meta = DOMAIN_META[domain];
  const Icon = meta.icon;

  const top = block.patterns[0];
  const rest = block.patterns.slice(1);

  // Standalone atoms = atoms NOT backing the top expanded pattern.
  const topBacking = new Set(top ? top.backing_atom_ids : []);
  const standalone: AtomMatch[] = block.atoms.filter(
    (a) => !topBacking.has(a.atom_id),
  );

  // Backing-evidence rail: resolve top.backing_atom_ids → AtomMatch objects
  // via intersection with block.atoms, then take the top 3 by
  // population_match_score desc. This restores claim+DOI provenance for the
  // expanded pattern (PatternCard renders IDs only).
  const backingAtoms: AtomMatch[] = top
    ? block.atoms
        .filter((a) => topBacking.has(a.atom_id))
        .sort((a, b) => b.population_match_score - a.population_match_score)
        .slice(0, 3)
    : [];

  const route = `/clients/${personaSlug}/${meta.hostRoute}`;
  const routeHref = meta.routeHash ? `${route}#${meta.routeHash}` : route;

  return (
    <GlassCard
      emphasis
      data-prescription-section
      innerClassName="flex flex-col gap-6 p-7"
    >
      {/* Header */}
      <header className="flex flex-wrap items-center gap-3">
        <Icon className="h-4 w-4 text-zinc-300" strokeWidth={1.5} />
        <h2 className="text-base font-semibold tracking-tight text-white">
          {meta.label}
        </h2>
        <ScorePill
          label="Confidence"
          value={formatPercent(confidence, 0)}
          emphasis
        />
        <span className="text-[0.65rem] text-zinc-500">
          {block.atoms.length} atom{block.atoms.length === 1 ? "" : "s"} ·{" "}
          {block.patterns.length} pattern
          {block.patterns.length === 1 ? "" : "s"}
        </span>
        <div className="ml-auto h-px flex-1 bg-white/[0.06]" />
      </header>

      {/* Top pattern — expanded inline. PatternCard is re-used as-is here;
          T03 may swap to a tighter inline render. */}
      {top ? <PatternCard pattern={top} /> : null}

      {/* Backing evidence rail — top 3 backing atoms with claim + DOI. */}
      {backingAtoms.length > 0 ? (
        <div className="flex flex-col gap-2 rounded-md border border-white/[0.06] bg-white/[0.015] px-4 py-3">
          <span className="text-[0.6rem] font-medium uppercase tracking-[0.12em] text-zinc-500">
            Backing evidence
          </span>
          <ul className="flex flex-col gap-2">
            {backingAtoms.map((a) => {
              const c = a.citations[0];
              return (
                <li
                  key={a.atom_id}
                  className="flex flex-wrap items-center gap-x-2 gap-y-1 text-[0.7rem] text-zinc-300"
                >
                  <span className="rounded bg-white/[0.04] px-1.5 py-0.5 font-mono text-[0.6rem] text-zinc-400">
                    {a.atom_id}
                  </span>
                  <span className="min-w-0 flex-1 truncate">
                    {truncate(a.claim, 140)}
                  </span>
                  {c ? (
                    <a
                      href={citationHref(c.id)}
                      target="_blank"
                      rel="noreferrer"
                      className="font-mono text-[0.6rem] text-zinc-400 underline-offset-2 hover:text-white hover:underline"
                    >
                      {c.id}
                    </a>
                  ) : null}
                </li>
              );
            })}
          </ul>
        </div>
      ) : null}

      {/* Remaining patterns: collapsed */}
      {rest.length > 0 ? (
        <div className="flex flex-col gap-2">
          {rest.map((p) => (
            <details
              key={p.pattern_id}
              className="group rounded-md border border-white/[0.06] bg-white/[0.015]"
            >
              <summary className="flex cursor-pointer list-none items-center gap-2 px-4 py-2.5 select-none">
                <ChevronRight
                  className="h-3.5 w-3.5 text-zinc-500 transition-transform group-open:rotate-90"
                  strokeWidth={1.75}
                />
                <span className="font-mono text-[0.6rem] text-zinc-400">
                  {p.pattern_id}
                </span>
                <span className="truncate text-[0.75rem] text-zinc-300">
                  {p.applies_because}
                </span>
                <span className="ml-auto font-mono text-[0.6rem] text-zinc-500">
                  {formatPercent(p.similarity, 0)}
                </span>
              </summary>
              <div className="px-4 pb-4">
                <PatternCard pattern={p} defaultOpen={false} />
              </div>
            </details>
          ))}
        </div>
      ) : null}

      {/* Standalone atoms: collapsed */}
      {standalone.length > 0 ? (
        <details className="group rounded-md border border-white/[0.06] bg-white/[0.015]">
          <summary className="flex cursor-pointer list-none items-center gap-2 px-4 py-2.5 select-none">
            <ChevronRight
              className="h-3.5 w-3.5 text-zinc-500 transition-transform group-open:rotate-90"
              strokeWidth={1.75}
            />
            <span className="text-[0.7rem] text-zinc-300">
              + {standalone.length} atom{standalone.length === 1 ? "" : "s"} in
              this domain
            </span>
          </summary>
          <div className="grid grid-cols-1 gap-3 p-4 md:grid-cols-2">
            {standalone.map((a, i) => (
              <AtomCard key={`${a.atom_id}-${i}`} atom={a} />
            ))}
          </div>
        </details>
      ) : null}

      {/* Footer link */}
      <a
        href={routeHref}
        className="inline-flex items-center gap-1.5 self-start text-[0.7rem] text-zinc-400 transition-colors hover:text-white"
      >
        Read full {meta.label.toLowerCase()} domain
        <ArrowUpRight className="h-3 w-3" strokeWidth={1.75} />
      </a>
    </GlassCard>
  );
}
