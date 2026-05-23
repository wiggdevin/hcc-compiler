"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { ChevronDown, Check } from "lucide-react";
import { cn } from "@/lib/utils";
import { PERSONAS, type Persona } from "@/lib/data/personas";
import { GradientAvatar } from "./gradient-avatar";

type Props = {
  active: Persona;
  /** Pathname suffix to keep when switching (e.g. "overview" / "diet"). */
  section: string;
};

export function PersonaSwitcher({ active, section }: Props) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDocClick = (e: MouseEvent) => {
      if (
        rootRef.current &&
        !rootRef.current.contains(e.target as Node)
      ) {
        setOpen(false);
      }
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") setOpen(false);
    };
    document.addEventListener("mousedown", onDocClick);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("mousedown", onDocClick);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div ref={rootRef} className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-haspopup="listbox"
        aria-expanded={open}
        className={cn(
          "flex items-center gap-2.5 rounded-full border border-white/10 bg-white/5 px-2.5 py-1 pr-3.5",
          "hover:border-white/20 hover:bg-white/[0.07] transition-colors",
          "focus:outline-none focus-visible:ring-2 focus-visible:ring-white/30",
        )}
      >
        <GradientAvatar initials={active.initials} size={24} />
        <span className="text-xs font-medium text-white">{active.displayName}</span>
        <ChevronDown
          className={cn(
            "h-3 w-3 text-zinc-400 transition-transform",
            open && "rotate-180",
          )}
        />
      </button>

      {open ? (
        <div
          role="listbox"
          className={cn(
            "absolute right-0 top-[calc(100%+8px)] z-50 w-72 overflow-hidden",
            "rounded-[12px] p-[1px] glass-shell",
          )}
        >
          <div className="rounded-[11px] bg-[#0b0b0d]/95 backdrop-blur-xl">
            <div className="border-b border-white/5 px-4 py-2.5">
              <p className="text-[0.65rem] font-medium uppercase tracking-[0.18em] text-zinc-500">
                Switch Client
              </p>
            </div>
            <ul className="max-h-[calc(100vh-160px)] overflow-auto scrollbar-hidden py-1">
              {PERSONAS.map((p) => (
                <li key={p.slug}>
                  <Link
                    href={`/clients/${p.slug}/${section}`}
                    onClick={() => setOpen(false)}
                    className={cn(
                      "flex items-center gap-3 px-3 py-2 transition-colors hover:bg-white/[0.04]",
                      p.slug === active.slug && "bg-white/[0.03]",
                    )}
                  >
                    <GradientAvatar initials={p.initials} size={28} />
                    <div className="min-w-0 flex-1">
                      <p className="truncate text-xs font-medium text-white">
                        {p.displayName}
                      </p>
                      <p className="truncate text-[0.65rem] text-zinc-500">
                        {p.tagline}
                      </p>
                    </div>
                    {p.slug === active.slug ? (
                      <Check className="h-3.5 w-3.5 shrink-0 text-white" />
                    ) : null}
                  </Link>
                </li>
              ))}
            </ul>
          </div>
        </div>
      ) : null}
    </div>
  );
}
