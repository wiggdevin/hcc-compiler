import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "HCC Compiler — Evidence-backed plans for health coaches",
  description:
    "Fill an intake form. Get a 6-domain nutrition and training plan with citations on every claim, delivered in 60 seconds.",
};

// Static generation — no auth dependency on this page.
export const dynamic = "force-static";

const VALUE_PROPS = [
  {
    heading: "Every recommendation cites a peer-reviewed source",
    body: "Coaches can audit every atom, trace each DOI, and hand clients a plan they can defend. No black-box outputs.",
  },
  {
    heading: "Constraint-aware from the first line",
    body: "Surgery history, thyroid medication, cycle phase, schedule limits, and renal flags all weave into the prescription — not appended as caveats after the fact.",
  },
  {
    heading: "60-second turnaround",
    body: "Fill the intake form, get a 6-domain plan across nutrition, training, sleep, supplementation, recovery, and lifestyle — ready to discuss at your next session.",
  },
] as const;

const HOW_IT_WORKS_STEPS = [
  {
    step: "01",
    heading: "Fill the intake",
    body: "Demographics, goals, constraints, contraindications, and current regimen — all collected in one structured form. Typed in five minutes, not forty.",
  },
  {
    step: "02",
    heading: "The compiler runs",
    body: "A 200+ atom evidence library, semantic citation matching, and a 2-layer confidence gate produce a tier-ranked prescription stack. No guessing, no hallucinated citations.",
  },
  {
    step: "03",
    heading: "You get a defensible plan",
    body: "PDF and Markdown exports, DOI-linked references, constraint notes flagged inline, and a confidence score per domain. Print it. Share it. Build on it.",
  },
] as const;

const FAQS_PREVIEW = [
  {
    q: "Can I use this without a biology background?",
    a: "Yes. The plan surfaces the constraint notes and flags that require professional judgment — you stay in control of what to prescribe.",
  },
  {
    q: "How are citations verified?",
    a: "Every atom in the library links to a DOI. The compiler rejects atoms that fail a two-stage citation gate at harvest time. Nothing lands in the library without a resolvable paper behind it.",
  },
];

export default function LandingPage() {
  return (
    <>
      {/* ── HERO ── */}
      <section className="mx-auto max-w-6xl px-6 pb-24 pt-20 text-center">
        <p className="mb-4 text-[0.7rem] font-semibold uppercase tracking-[0.2em] text-emerald-400">
          Built for independent coaches and RDs
        </p>
        <h1 className="mx-auto max-w-3xl text-balance text-[2.6rem] font-semibold leading-[1.12] tracking-tight text-white sm:text-[3.2rem]">
          Evidence-backed nutrition and training plans in 60 seconds
        </h1>
        <p className="mx-auto mt-6 max-w-xl text-balance text-base leading-relaxed text-zinc-400">
          We compile the research so you can spend your time coaching. Fill the
          intake form, and HCC Compiler produces a 6-domain plan with a
          peer-reviewed citation on every claim.
        </p>
        <div className="mt-10 flex flex-wrap items-center justify-center gap-4">
          <Link
            href="/sign-in"
            className="rounded-md bg-emerald-500 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-emerald-400"
          >
            Sign up — free during beta
          </Link>
          <Link
            href="/samples/carl-sample-plan.md"
            target="_blank"
            rel="noopener noreferrer"
            className="rounded-md border border-white/10 px-5 py-2.5 text-sm font-medium text-zinc-200 transition-colors hover:border-white/20 hover:text-white"
          >
            See a sample plan
          </Link>
        </div>

        {/* Social proof strip */}
        <p className="mt-8 text-[0.7rem] text-zinc-600">
          200+ citations in the library · 9 sample personas · all DOI-linked
        </p>
      </section>

      {/* ── VALUE PROPS ── */}
      <section className="border-t border-white/[0.06] py-20">
        <div className="mx-auto max-w-6xl px-6">
          <div className="grid gap-8 sm:grid-cols-3">
            {VALUE_PROPS.map(({ heading, body }) => (
              <div key={heading} className="flex flex-col gap-3">
                <div className="h-0.5 w-8 rounded-full bg-emerald-500" />
                <h3 className="text-[0.9rem] font-semibold leading-snug text-white">
                  {heading}
                </h3>
                <p className="text-[0.8rem] leading-relaxed text-zinc-400">
                  {body}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── HOW IT WORKS (summary) ── */}
      <section className="border-t border-white/[0.06] py-20">
        <div className="mx-auto max-w-6xl px-6">
          <p className="mb-2 text-[0.68rem] font-semibold uppercase tracking-[0.2em] text-zinc-500">
            The workflow
          </p>
          <h2 className="mb-12 text-[1.6rem] font-semibold tracking-tight text-white">
            Three steps from intake to defensible plan
          </h2>
          <div className="grid gap-8 sm:grid-cols-3">
            {HOW_IT_WORKS_STEPS.map(({ step, heading, body }) => (
              <div
                key={step}
                className="flex flex-col gap-3 rounded-xl border border-white/[0.07] bg-white/[0.02] p-6"
              >
                <span className="font-mono text-[0.65rem] font-medium tracking-widest text-emerald-400">
                  {step}
                </span>
                <h3 className="text-[0.9rem] font-semibold text-white">
                  {heading}
                </h3>
                <p className="text-[0.78rem] leading-relaxed text-zinc-400">
                  {body}
                </p>
              </div>
            ))}
          </div>
          <p className="mt-8 text-[0.75rem] text-zinc-500">
            <Link
              href="/how-it-works"
              className="text-zinc-300 underline underline-offset-2 hover:text-white"
            >
              Full walkthrough with screenshots
            </Link>
          </p>
        </div>
      </section>

      {/* ── PRICING TEASER ── */}
      <section className="border-t border-white/[0.06] py-20">
        <div className="mx-auto max-w-6xl px-6">
          <div className="rounded-xl border border-white/[0.07] bg-white/[0.02] p-8 sm:p-10">
            <p className="mb-2 text-[0.68rem] font-semibold uppercase tracking-[0.2em] text-zinc-500">
              Pricing
            </p>
            <h2 className="mb-4 text-[1.5rem] font-semibold tracking-tight text-white">
              Free during beta
            </h2>
            <p className="max-w-lg text-[0.82rem] leading-relaxed text-zinc-400">
              The compiler is free while we are in closed beta. After launch,
              plans will be available via a monthly subscription for active
              coaches and per-pack credits for lower-volume use.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-4">
              <Link
                href="/sign-in"
                className="rounded-md bg-emerald-500 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-emerald-400"
              >
                Try with a sample client
              </Link>
              <Link
                href="/pricing"
                className="text-[0.78rem] text-zinc-400 underline underline-offset-2 hover:text-white"
              >
                See full pricing details
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ── FAQ TEASER ── */}
      <section className="border-t border-white/[0.06] py-20">
        <div className="mx-auto max-w-6xl px-6">
          <p className="mb-2 text-[0.68rem] font-semibold uppercase tracking-[0.2em] text-zinc-500">
            Common questions
          </p>
          <h2 className="mb-10 text-[1.5rem] font-semibold tracking-tight text-white">
            What coaches ask us
          </h2>
          <div className="flex flex-col gap-6">
            {FAQS_PREVIEW.map(({ q, a }) => (
              <div
                key={q}
                className="rounded-lg border border-white/[0.07] p-6"
              >
                <p className="mb-2 text-[0.85rem] font-semibold text-white">
                  {q}
                </p>
                <p className="text-[0.78rem] leading-relaxed text-zinc-400">
                  {a}
                </p>
              </div>
            ))}
          </div>
          <p className="mt-6 text-[0.75rem] text-zinc-500">
            <Link
              href="/faq"
              className="text-zinc-300 underline underline-offset-2 hover:text-white"
            >
              Read all FAQs
            </Link>
          </p>
        </div>
      </section>

      {/* ── SIGN-UP CTA ── */}
      <section className="border-t border-white/[0.06] py-20">
        <div className="mx-auto max-w-6xl px-6 text-center">
          <h2 className="mb-4 text-[1.8rem] font-semibold tracking-tight text-white">
            Start with a real client this week
          </h2>
          <p className="mx-auto mb-8 max-w-md text-[0.82rem] leading-relaxed text-zinc-400">
            Sign up, fill an intake, and have a citation-backed plan ready
            before your next session.
          </p>
          <Link
            href="/sign-in"
            className="inline-block rounded-md bg-emerald-500 px-6 py-3 text-sm font-medium text-white transition-colors hover:bg-emerald-400"
          >
            Sign up — free during beta
          </Link>
        </div>
      </section>
    </>
  );
}
