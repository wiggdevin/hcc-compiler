"use client";

import { Calendar, CalendarDays, Sparkles, MessageCircle } from "lucide-react";
import { cn } from "@/lib/utils";

export type TabKey = "today" | "week" | "why" | "coach";

const TABS: { key: TabKey; label: string; Icon: typeof Calendar }[] = [
  { key: "today", label: "Today", Icon: Calendar },
  { key: "week", label: "Week", Icon: CalendarDays },
  { key: "why", label: "Why", Icon: Sparkles },
  { key: "coach", label: "Coach", Icon: MessageCircle },
];

export function BottomNav({
  active,
  onChange,
}: {
  active: TabKey;
  onChange: (k: TabKey) => void;
}) {
  return (
    <nav
      className="fixed inset-x-0 bottom-0 z-30 mx-auto w-full max-w-md border-t border-white/10 bg-black/80 px-2 pb-[max(env(safe-area-inset-bottom),0.5rem)] pt-2 backdrop-blur-xl"
      aria-label="Plan sections"
    >
      <ul className="grid grid-cols-4">
        {TABS.map(({ key, label, Icon }) => {
          const isActive = active === key;
          return (
            <li key={key}>
              <button
                onClick={() => onChange(key)}
                className={cn(
                  "flex w-full flex-col items-center gap-0.5 rounded-lg py-2 text-[10px] uppercase tracking-wider transition",
                  isActive
                    ? "text-emerald-300"
                    : "text-white/50 hover:text-white/80",
                )}
                aria-pressed={isActive}
              >
                <Icon className="h-5 w-5" />
                <span className="text-[11px] font-medium normal-case tracking-normal">
                  {label}
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </nav>
  );
}
