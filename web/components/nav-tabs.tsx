"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

interface Tab {
  href: string;
  label: string;
  /** Section key for client-switcher to preserve. */
  section: string;
}

interface Props {
  personaSlug: string;
}

export function NavTabs({ personaSlug }: Props) {
  const pathname = usePathname() ?? "";
  const base = `/clients/${personaSlug}`;

  const tabs: Tab[] = [
    { href: `${base}/intake`, label: "Intake & Status", section: "intake" },
    { href: `${base}/overview`, label: "Overview", section: "overview" },
    { href: `${base}/diet`, label: "Diet Matrix", section: "diet" },
    { href: `${base}/workout`, label: "Movement Protocol", section: "workout" },
    { href: `${base}/recovery`, label: "Recovery & Supplements", section: "recovery" },
    { href: `${base}/literature`, label: "Literature", section: "literature" },
  ];

  return (
    <nav className="hidden md:flex items-center gap-8 text-xs font-medium">
      {tabs.map((t) => {
        const active = pathname === t.href;
        return (
          <Link
            key={t.href}
            href={t.href}
            className={cn(
              "relative whitespace-nowrap py-1 transition-colors",
              active
                ? "text-white"
                : "text-zinc-400 hover:text-white",
            )}
          >
            {t.label}
            {active ? (
              <span className="absolute -bottom-[1px] left-0 h-[1px] w-full bg-white" />
            ) : null}
          </Link>
        );
      })}
    </nav>
  );
}

export function getCurrentSection(pathname: string): string {
  const m = pathname.match(/\/clients\/[^/]+\/([^/?#]+)/);
  return m?.[1] ?? "overview";
}
