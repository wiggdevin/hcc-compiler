import { AlertTriangle } from "lucide-react";
import { cleanWarning } from "@/lib/format";

interface Props {
  warnings: string[];
}

export function WarningRow({ warnings }: Props) {
  if (warnings.length === 0) return null;
  return (
    <div className="space-y-1.5">
      {warnings.map((w, i) => (
        <div
          key={i}
          className="flex items-start gap-2 rounded-md border border-amber-400/15 bg-amber-400/[0.04] px-3 py-2"
        >
          <AlertTriangle
            className="mt-0.5 h-3 w-3 shrink-0 text-amber-300"
            strokeWidth={1.75}
          />
          <p className="text-[0.7rem] leading-relaxed text-amber-100/90">
            {cleanWarning(w)}
          </p>
        </div>
      ))}
    </div>
  );
}
