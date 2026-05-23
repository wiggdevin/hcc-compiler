import type { CSSProperties } from "react";
import { cn } from "@/lib/utils";
import { formatPercent } from "@/lib/format";

interface Props {
  value: number; // 0..1
  label?: string;
  sublabel?: string;
  size?: number; // px
  className?: string;
}

/**
 * Radial confidence indicator. Pure CSS — the conic gradient is driven by
 * the `--value` custom property on `.score-ring-track`.
 */
export function ScoreRing({
  value,
  label = "Plan Confidence",
  sublabel,
  size = 280,
  className,
}: Props) {
  const trackStyle = {
    "--value": value.toFixed(4),
  } as CSSProperties;

  return (
    <div
      className={cn("relative animate-scale-in", className)}
      style={{ width: size, height: size }}
    >
      <div
        className="absolute inset-0 rounded-full score-ring-track"
        style={trackStyle}
      />
      {/* Inner cutout */}
      <div className="absolute inset-[14px] rounded-full bg-[#09090b]" />
      {/* Inner subtle ring */}
      <div className="absolute inset-[14px] rounded-full border border-white/[0.04]" />
      <div className="absolute inset-0 grid place-items-center text-center">
        <div className="flex flex-col items-center gap-1">
          <span className="text-5xl font-semibold tabular tracking-tight text-white">
            {formatPercent(value, 0)}
          </span>
          <span className="text-[0.65rem] font-medium uppercase tracking-[0.22em] text-zinc-500">
            {label}
          </span>
          {sublabel ? (
            <span className="mt-1 text-[0.6rem] text-zinc-600">{sublabel}</span>
          ) : null}
        </div>
      </div>
    </div>
  );
}
