import { cn } from "@/lib/utils";

interface Props {
  label: string;
  value: string;
  className?: string;
  emphasis?: boolean;
}

/** Inline numeric badge for atom score clusters. */
export function ScorePill({ label, value, className, emphasis }: Props) {
  return (
    <span
      className={cn(
        "inline-flex items-baseline gap-1.5 rounded-md border px-2 py-1",
        emphasis
          ? "border-white/20 bg-white/[0.06]"
          : "border-white/10 bg-white/[0.025]",
        className,
      )}
    >
      <span className="text-[0.55rem] font-medium uppercase tracking-wider text-zinc-500">
        {label}
      </span>
      <span className="text-[0.7rem] font-semibold text-white tabular">
        {value}
      </span>
    </span>
  );
}
