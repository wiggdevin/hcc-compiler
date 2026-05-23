import type { ReactNode } from "react";
import { cn } from "@/lib/utils";

interface Props {
  label: string;
  value: ReactNode;
  className?: string;
  divider?: boolean;
}

export function StatRow({ label, value, className, divider = true }: Props) {
  return (
    <div
      className={cn(
        "flex items-baseline justify-between gap-4 py-2",
        divider && "border-b border-white/[0.06]",
        className,
      )}
    >
      <span className="text-[0.7rem] font-medium tracking-wide text-zinc-500">
        {label}
      </span>
      <span className="text-sm font-medium text-white tabular">{value}</span>
    </div>
  );
}
