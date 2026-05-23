import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface Stat {
  label: string;
  value: ReactNode;
  hint?: string;
}

interface Props {
  stats: Stat[];
  className?: string;
  /** "left" right-aligns labels; "right" left-aligns them. */
  align?: "left" | "right";
}

/**
 * Stacked stat cluster used in Overview hero left/right rails.
 * Each stat is large+tabular for "score-ish" data.
 */
export function ScoreCluster({ stats, className, align = "left" }: Props) {
  return (
    <dl className={cn("flex flex-col gap-6", className)}>
      {stats.map((s, i) => (
        <div
          key={i}
          className={cn(
            "flex flex-col gap-1",
            align === "right" && "text-right items-end",
          )}
        >
          <dt className="text-[0.65rem] font-semibold uppercase tracking-[0.22em] text-zinc-500">
            {s.label}
          </dt>
          <dd className="text-2xl font-semibold tabular tracking-tight text-white">
            {s.value}
          </dd>
          {s.hint ? (
            <dd className="text-[0.65rem] text-zinc-500">{s.hint}</dd>
          ) : null}
        </div>
      ))}
    </dl>
  );
}
