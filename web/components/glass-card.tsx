import type { ComponentPropsWithoutRef, ReactNode } from "react";
import { cn } from "@/lib/utils";

type DivProps = ComponentPropsWithoutRef<"div">;

interface GlassCardProps extends DivProps {
  children: ReactNode;
  innerClassName?: string;
  /** Slightly lifts the gradient shell — for hero / emphasis cards. */
  emphasis?: boolean;
}

/**
 * The signature primitive. Outer 1px gradient padding wraps an inner surface
 * at radius 11 — so the gradient reads as a hairline frame at radius 12.
 */
export function GlassCard({
  children,
  className,
  innerClassName,
  emphasis = false,
  ...rest
}: GlassCardProps) {
  return (
    <div
      className={cn(
        "p-[1px] rounded-[12px] glass-shell",
        emphasis && "shadow-[0_30px_80px_-40px_rgba(59,130,246,0.25)]",
        className,
      )}
      {...rest}
    >
      <div
        className={cn(
          "rounded-[11px] bg-[#0b0b0d] backdrop-blur-xl",
          innerClassName,
        )}
      >
        {children}
      </div>
    </div>
  );
}
