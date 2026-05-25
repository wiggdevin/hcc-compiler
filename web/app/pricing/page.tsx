import Link from "next/link";

export const metadata = {
  title: "Pricing · Aura Clinic",
  description: "Evidence-backed nutrition and training plans for health coaches.",
};

export default function PricingPage() {
  return (
    <main className="mx-auto w-full max-w-5xl px-4 py-16 md:px-8">
      <header className="mb-16 text-center">
        <p className="text-xs font-medium uppercase tracking-[0.2em] text-emerald-300/70">
          Pricing
        </p>
        <h1 className="mt-3 text-4xl font-light tracking-tight text-white md:text-5xl">
          Simple, transparent pricing
        </h1>
        <p className="mx-auto mt-4 max-w-xl text-sm leading-relaxed text-white/60">
          One flat monthly rate for active coaches. Single-credit packs for coaches who
          compile plans less frequently — no subscription required.
        </p>
      </header>

      <div className="grid gap-6 md:grid-cols-2">
        {/* Active Coach */}
        <div className="relative rounded-2xl border border-emerald-400/30 bg-white/[0.03] p-8 backdrop-blur-sm">
          <span className="absolute right-6 top-6 rounded-full border border-emerald-400/40 bg-emerald-500/20 px-2.5 py-0.5 text-xs font-medium text-emerald-100">
            Most popular
          </span>
          <p className="text-xs font-medium uppercase tracking-wider text-emerald-300/70">
            Active Coach
          </p>
          <div className="mt-4 flex items-end gap-1">
            <span className="text-5xl font-light tabular-nums text-white">$79</span>
            <span className="mb-2 text-sm text-white/50">/ month</span>
          </div>
          <p className="mt-3 text-sm text-white/60">
            Unlimited evidence pack compiles. Built for coaches with 4+ active clients
            per month.
          </p>

          <ul className="mt-6 space-y-3 text-sm text-white/80">
            {[
              "Unlimited plan compiles",
              "All 7 goal types",
              "Constraint-aware prescriptions",
              "Downloadable Markdown + JSON",
              "PDF export (coming Phase 5)",
              "Priority support",
            ].map((f) => (
              <li key={f} className="flex items-center gap-2">
                <svg
                  className="h-4 w-4 shrink-0 text-emerald-400"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                {f}
              </li>
            ))}
          </ul>

          <Link
            href="/api/stripe/checkout"
            className="mt-8 flex w-full items-center justify-center rounded-lg border border-emerald-400/40 bg-emerald-500/20 py-3 text-sm font-semibold text-emerald-100 transition hover:bg-emerald-500/30"
          >
            Get started
          </Link>
          <p className="mt-2 text-center text-xs text-white/40">
            Cancel anytime. No long-term contract.
          </p>
        </div>

        {/* Single Plan Credit */}
        <div className="rounded-2xl border border-white/10 bg-white/[0.02] p-8 backdrop-blur-sm">
          <p className="text-xs font-medium uppercase tracking-wider text-white/50">
            Single Plan
          </p>
          <div className="mt-4 flex items-end gap-1">
            <span className="text-5xl font-light tabular-nums text-white">$29</span>
            <span className="mb-2 text-sm text-white/50">/ pack</span>
          </div>
          <p className="mt-3 text-sm text-white/60">
            One credit, one evidence pack. No subscription required. Great for trying
            the compiler or occasional use.
          </p>

          <ul className="mt-6 space-y-3 text-sm text-white/80">
            {[
              "One evidence pack compile",
              "All 7 goal types",
              "Constraint-aware prescriptions",
              "Downloadable Markdown + JSON",
              "Credits never expire",
              "Stack multiple packs",
            ].map((f) => (
              <li key={f} className="flex items-center gap-2">
                <svg
                  className="h-4 w-4 shrink-0 text-white/40"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  strokeWidth={2}
                >
                  <path strokeLinecap="round" strokeLinejoin="round" d="M5 13l4 4L19 7" />
                </svg>
                {f}
              </li>
            ))}
          </ul>

          <Link
            href="/api/stripe/checkout?plan=credits"
            className="mt-8 flex w-full items-center justify-center rounded-lg border border-white/15 bg-white/[0.06] py-3 text-sm font-medium text-white transition hover:bg-white/[0.12]"
          >
            Buy a credit
          </Link>
          <p className="mt-2 text-center text-xs text-white/40">One-time payment, no recurring charge.</p>
        </div>
      </div>

      {/* FAQ */}
      <section className="mt-20">
        <h2 className="text-xl font-light text-white">Frequently asked questions</h2>
        <div className="mt-8 space-y-6 text-sm">
          {[
            {
              q: "What is a plan credit?",
              a: "One credit compiles one complete evidence pack for one client — a JSON data file, a Markdown narrative, and (soon) a branded PDF. Credits never expire.",
            },
            {
              q: "Can I switch from credits to a subscription?",
              a: "Yes. Subscribe any time from your billing page. Remaining credits stay on your account.",
            },
            {
              q: "How does cancellation work?",
              a: "Subscriptions stay active until the end of the current billing period. You will not be charged again after canceling, and you keep access until the period ends.",
            },
            {
              q: "Is my client data stored?",
              a: "Intake data is stored in your account on Supabase-hosted infrastructure. Compiled plans are stored as signed URLs accessible only to you. We never share client data.",
            },
            {
              q: "Not medical advice?",
              a: "Correct. Aura Clinic generates evidence references, not prescriptions. Coaches must apply professional judgment to every plan before delivering it to a client.",
            },
          ].map(({ q, a }) => (
            <div key={q} className="rounded-xl border border-white/10 bg-white/[0.02] p-5">
              <p className="font-medium text-white">{q}</p>
              <p className="mt-2 text-white/60 leading-relaxed">{a}</p>
            </div>
          ))}
        </div>
      </section>

      <footer className="mt-16 border-t border-white/10 pt-6 text-xs text-white/40">
        Not medical advice. Coaches must apply professional judgment. Plans are evidence
        references, not prescriptions.
      </footer>
    </main>
  );
}
