import { cn } from "@/lib/utils";
import { evidenceDescriptor } from "@/lib/format";
import type { EvidenceLevel } from "@/lib/data/types";

const STYLES: Record<EvidenceLevel, string> = {
  L1: "bg-white/[0.12] border-white/30 text-white",
  L2: "bg-white/[0.07] border-white/20 text-white",
  L3: "bg-white/[0.04] border-white/15 text-zinc-200",
  L4: "bg-transparent border-white/10 text-zinc-400",
};

export function EvidenceLevelChip({
  level,
  showDescriptor = false,
  className,
}: {
  level: EvidenceLevel;
  showDescriptor?: boolean;
  className?: string;
}) {
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-[0.6rem] font-semibold tabular tracking-wider uppercase",
        STYLES[level],
        className,
      )}
      title={evidenceDescriptor(level)}
    >
      {level}
      {showDescriptor ? (
        <span className="font-medium normal-case tracking-normal text-zinc-400">
          {evidenceDescriptor(level)}
        </span>
      ) : null}
    </span>
  );
}
