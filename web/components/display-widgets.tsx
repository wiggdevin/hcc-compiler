/**
 * Read-only form widgets — visually identical to interactive controls but
 * not actually editable. Used by the Intake page to render captured data
 * in a way that *looks* like a live form.
 */
import { Check, Minus } from "lucide-react";
import { cn } from "@/lib/utils";

export function DisplayInput({
  label,
  value,
  className,
}: {
  label: string;
  value: string | number;
  className?: string;
}) {
  return (
    <div className={cn("flex flex-col gap-1.5", className)}>
      <label className="text-[0.65rem] font-medium uppercase tracking-[0.12em] text-zinc-500">
        {label}
      </label>
      <div className="rounded-md border border-white/10 bg-zinc-900/40 px-3 py-2 text-sm text-zinc-200">
        {value}
      </div>
    </div>
  );
}

export function DisplaySlider({
  label,
  value,
  min = 0,
  max = 1,
  format,
}: {
  label: string;
  value: number;
  min?: number;
  max?: number;
  format?: (v: number) => string;
}) {
  const pct = Math.max(0, Math.min(1, (value - min) / (max - min)));
  return (
    <div className="flex flex-col gap-2 pt-2">
      <div className="flex items-end justify-between">
        <label className="text-[0.65rem] font-medium uppercase tracking-[0.12em] text-zinc-500">
          {label}
        </label>
        <span className="text-xs font-medium text-white tabular">
          {format ? format(value) : value.toFixed(2)}
        </span>
      </div>
      <div className="relative h-1 w-full overflow-visible rounded-full bg-zinc-800">
        <div
          className="absolute left-0 top-0 h-full rounded-full bg-white"
          style={{ width: `${pct * 100}%` }}
        />
        <div
          className="absolute top-1/2 h-3 w-3 -translate-x-1/2 -translate-y-1/2 rounded-full border-2 border-zinc-950 bg-white"
          style={{ left: `${pct * 100}%` }}
        />
      </div>
    </div>
  );
}

export function DisplayToggle({
  label,
  on,
}: {
  label: string;
  on: boolean;
}) {
  return (
    <div className="flex items-center justify-between gap-3 pt-2">
      <label className="text-[0.65rem] font-medium uppercase tracking-[0.12em] text-zinc-500">
        {label}
      </label>
      <div
        className={cn(
          "relative h-4 w-8 rounded-full border transition-colors",
          on
            ? "border-white/40 bg-white/15"
            : "border-white/10 bg-zinc-800",
        )}
      >
        <div
          className={cn(
            "absolute top-1/2 h-3 w-3 -translate-y-1/2 rounded-full transition-all",
            on ? "left-[calc(100%-14px)] bg-white" : "left-[2px] bg-zinc-500",
          )}
        />
      </div>
    </div>
  );
}

export function DisplayCheckbox({
  label,
  detail,
  checked = true,
}: {
  label: string;
  detail?: string;
  checked?: boolean;
}) {
  return (
    <div
      className={cn(
        "flex items-start gap-3 rounded-md p-2",
        checked && "bg-white/[0.035]",
      )}
    >
      <div
        className={cn(
          "mt-0.5 grid h-4 w-4 shrink-0 place-items-center rounded border transition-colors",
          checked
            ? "border-white bg-white"
            : "border-zinc-600 bg-zinc-900",
        )}
      >
        {checked ? (
          <Check className="h-3 w-3 text-[#09090b]" strokeWidth={3} />
        ) : (
          <Minus className="h-3 w-3 text-zinc-500" />
        )}
      </div>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-medium text-white">{label}</p>
        {detail ? (
          <p className="mt-0.5 text-[0.65rem] text-zinc-500">{detail}</p>
        ) : null}
      </div>
    </div>
  );
}
