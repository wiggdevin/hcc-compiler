import { cn } from "@/lib/utils";

interface Props {
  initials: string;
  size?: number;
  className?: string;
}

/**
 * Deterministic gradient circle keyed off the initials — avoids photo PII
 * while still giving each persona a recognisable visual.
 */
export function GradientAvatar({ initials, size = 40, className }: Props) {
  const hash = Array.from(initials).reduce(
    (a, ch) => (a * 33 + ch.charCodeAt(0)) >>> 0,
    5381,
  );
  const hue1 = hash % 360;
  const hue2 = (hue1 + 40) % 360;

  return (
    <div
      className={cn(
        "relative shrink-0 overflow-hidden rounded-full border border-white/15",
        className,
      )}
      style={{
        width: size,
        height: size,
        background: `linear-gradient(135deg, hsl(${hue1} 30% 28%) 0%, hsl(${hue2} 35% 18%) 100%)`,
      }}
    >
      <span
        className="absolute inset-0 flex items-center justify-center font-medium text-white/85 tabular"
        style={{ fontSize: Math.round(size * 0.36), letterSpacing: "0.04em" }}
      >
        {initials}
      </span>
    </div>
  );
}
