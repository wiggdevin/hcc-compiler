import type { LucideIcon } from "lucide-react";
import type { ReactNode } from "react";
import { GlassCard } from "./glass-card";

interface Props {
  icon: LucideIcon;
  title: string;
  children: ReactNode;
}

export function IntakePanel({ icon: Icon, title, children }: Props) {
  return (
    <GlassCard innerClassName="p-5 flex flex-col gap-5">
      <h2 className="flex items-center gap-2 text-sm font-semibold tracking-tight text-white">
        <Icon className="h-4 w-4" strokeWidth={1.5} />
        {title}
      </h2>
      <div className="space-y-4">{children}</div>
    </GlassCard>
  );
}
