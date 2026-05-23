import type { LucideIcon } from "lucide-react";
import type { DomainBlock } from "@/lib/data/types";
import { AtomCard } from "./atom-card";
import { PatternCard } from "./pattern-card";

interface Props {
  icon: LucideIcon;
  label: string;
  block: DomainBlock;
  id?: string;
}

export function DomainSection({ icon: Icon, label, block, id }: Props) {
  const isEmpty = block.atoms.length === 0 && block.patterns.length === 0;
  return (
    <section id={id} className="scroll-mt-24">
      <header className="mb-6 flex items-center gap-3">
        <Icon className="h-4 w-4 text-zinc-400" strokeWidth={1.5} />
        <h2 className="text-xs font-semibold uppercase tracking-[0.22em] text-zinc-200">
          {label}
        </h2>
        <span className="text-[0.65rem] text-zinc-500">
          {block.patterns.length} pattern{block.patterns.length === 1 ? "" : "s"} ·{" "}
          {block.atoms.length} atom{block.atoms.length === 1 ? "" : "s"}
        </span>
        <div className="ml-3 h-px flex-1 bg-white/[0.06]" />
      </header>

      {isEmpty ? (
        <p className="text-sm italic text-zinc-600">
          No recommendations in this domain for this client.
        </p>
      ) : (
        <>
          {block.patterns.length > 0 ? (
            <div className="stagger mb-8 flex flex-col gap-4">
              {block.patterns.map((p, i) => (
                <PatternCard
                  key={p.pattern_id}
                  pattern={p}
                  defaultOpen={i === 0}
                />
              ))}
            </div>
          ) : null}

          {block.atoms.length > 0 ? (
            <div className="max-w-[1000px] mx-auto">
              <div className="stagger grid grid-cols-1 gap-4 md:grid-cols-2">
                {block.atoms.map((a, i) => (
                  <AtomCard key={`${a.atom_id}-${i}`} atom={a} />
                ))}
              </div>
            </div>
          ) : null}
        </>
      )}
    </section>
  );
}
