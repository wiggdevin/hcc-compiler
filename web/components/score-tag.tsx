import type { LucideIcon } from "lucide-react";
import { cn } from "@/lib/utils";
import { formatPercent } from "@/lib/format";

interface Props {
  icon: LucideIcon;
  label: string;
  value: number;
  className?: string;
  /** "left" → bio-line extends to the right (tag sits to the left of anchor) */
  side?: "left" | "right";
  /** Stagger delay in seconds (defaults to 0). */
  delay?: number;
}

/**
 * Floating biometric tag — the AURA bio-tag pattern repurposed as a
 * domain-confidence label hung off the Overview score ring.
 */
export function ScoreTag({
  icon: Icon,
  label,
  value,
  className,
  side = "right",
  delay = 0,
}: Props) {
  return (
    <div
      className={cn(
        "absolute z-20 flex items-center gap-2 whitespace-nowrap",
        side === "right" ? "flex-row" : "flex-row-reverse",
        className,
      )}
    >
      <span
        className={cn(
          "bio-line h-[1px] w-12 animate-bio-line",
          side === "left" && "origin-right",
        )}
        style={{ "--delay": `${0.4 + delay}s` } as React.CSSProperties}
        aria-hidden
      />
      <span
        className="flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.05] px-3 py-1.5 backdrop-blur-md animate-fade-up"
        style={{ animationDelay: `${0.6 + delay}s` }}
      >
        <Icon className="h-3 w-3 text-zinc-300" strokeWidth={1.5} />
        <span className="text-[0.6rem] font-semibold uppercase tracking-[0.16em] text-zinc-300">
          {label}
        </span>
        <span className="text-[0.7rem] font-medium text-white tabular">
          {formatPercent(value, 0)}
        </span>
      </span>
    </div>
  );
}
