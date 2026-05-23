"use client";

import type { ReactNode } from "react";
import { Printer } from "lucide-react";

interface Props {
  children: ReactNode;
}

/**
 * Small client component — triggers the browser print dialog so the print
 * stylesheet in globals.css can take over. Matches the markdown download
 * anchor visually.
 */
export function PrintButton({ children }: Props) {
  return (
    <button
      type="button"
      onClick={() => window.print()}
      className="inline-flex items-center gap-2 rounded-md border border-white/10 bg-white/[0.025] px-3.5 py-2 text-[0.75rem] font-medium text-zinc-200 transition-colors hover:border-white/20 hover:bg-white/[0.05] hover:text-white"
    >
      <Printer className="h-3.5 w-3.5" strokeWidth={1.5} />
      {children}
    </button>
  );
}
