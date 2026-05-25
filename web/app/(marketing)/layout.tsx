import type { ReactNode } from "react";
import Link from "next/link";

/**
 * Minimal marketing shell — lighter than the coach dashboard layout.
 * No AmbientBg, no auth checks. Static-friendly.
 */
export default function MarketingLayout({ children }: { children: ReactNode }) {
  return (
    <div className="flex min-h-screen flex-col">
      {/* ── Nav ── */}
      <header className="sticky top-0 z-40 border-b border-white/[0.06] bg-[var(--bg)]/90 backdrop-blur-sm">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-6">
          <Link
            href="/"
            className="text-[0.8rem] font-semibold tracking-wide text-white"
          >
            HCC Compiler
          </Link>
          <nav className="flex items-center gap-6">
            <Link
              href="/how-it-works"
              className="text-[0.75rem] text-zinc-400 transition-colors hover:text-white"
            >
              How it works
            </Link>
            <Link
              href="/faq"
              className="text-[0.75rem] text-zinc-400 transition-colors hover:text-white"
            >
              FAQ
            </Link>
            <Link
              href="/pricing"
              className="text-[0.75rem] text-zinc-400 transition-colors hover:text-white"
            >
              Pricing
            </Link>
            <Link
              href="/sign-in"
              className="rounded-md bg-emerald-500 px-3.5 py-1.5 text-[0.75rem] font-medium text-white transition-colors hover:bg-emerald-400"
            >
              Sign up — free during beta
            </Link>
          </nav>
        </div>
      </header>

      {/* ── Page content ── */}
      <main className="flex-1">{children}</main>

      {/* ── Footer ── */}
      <footer className="border-t border-white/[0.06] py-10">
        <div className="mx-auto max-w-6xl px-6">
          <div className="flex flex-col items-start justify-between gap-6 sm:flex-row sm:items-center">
            <p className="text-[0.7rem] leading-relaxed text-zinc-500">
              HCC Compiler is a reference tool for qualified health coaches and
              registered dietitians. Plans are evidence references, not
              prescriptions. Not medical advice. Coaches must apply professional
              judgment before acting on any recommendation.
            </p>
            <div className="flex shrink-0 gap-4">
              <Link
                href="/how-it-works"
                className="text-[0.7rem] text-zinc-500 hover:text-zinc-300"
              >
                How it works
              </Link>
              <Link
                href="/faq"
                className="text-[0.7rem] text-zinc-500 hover:text-zinc-300"
              >
                FAQ
              </Link>
              <Link
                href="/pricing"
                className="text-[0.7rem] text-zinc-500 hover:text-zinc-300"
              >
                Pricing
              </Link>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}
