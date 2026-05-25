import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "FAQ — HCC Compiler",
  description:
    "Common questions from coaches about the evidence library, citation verification, safety flags, and pricing.",
};

export const dynamic = "force-static";

const FAQS = [
  {
    category: "The evidence library",
    items: [
      {
        q: "Where do the citations come from?",
        a: "Every atom in the library is harvested from PubMed and Crossref. The harvest pipeline requires a resolvable DOI and a structured abstract before an atom is accepted. Papers that fail DOI validation are discarded at harvest time, not patched after the fact.",
      },
      {
        q: "How often is the library updated?",
        a: "The library is versioned. Each plan records the library version it was built against so you can tell whether a newer version would change the recommendations. We publish library updates when a meaningful volume of new evidence warrants it — not on a fixed calendar schedule.",
      },
      {
        q: "Can I trust citations from an AI system?",
        a: "The compiler does not generate citations. It retrieves them. Atoms are pre-indexed by human curation plus automated PubMed/Crossref lookup. The two-layer citation gate at harvest time is the trust signal — if a DOI does not resolve to a real paper, the atom is rejected. What you see in a plan has already cleared that gate.",
      },
      {
        q: "How many citations does a typical plan include?",
        a: "A six-domain plan for a client with moderate complexity typically surfaces 15–40 unique citations across atoms and patterns. Clients with more constraints generate more safety-flag matches, which adds citation volume. Carl, our strength-with-CKD persona, generates 7 safety preflight hits and 20+ backing references.",
      },
    ],
  },
  {
    category: "Constraint handling",
    items: [
      {
        q: "What counts as a contraindication?",
        a: "Contraindications are conditions that trigger a safety preflight match — things like CKD, T2DM, dialysis, pre-existing cardiovascular disease, active cancer treatment, and post-surgical states. The intake form collects them as a typed list with a detail field. The compiler checks every atom and pattern against this list before building the prescription stack.",
      },
      {
        q: "What happens when a contraindication matches a recommendation?",
        a: "The plan flags it explicitly. The flagged atom or pattern is still shown — the coach needs to see what the evidence says — but the flag is printed at the top of the plan and inline at the prescription level. The decision to modify or exclude that recommendation belongs to the coach, not the compiler.",
      },
      {
        q: "Does the compiler handle cycle-phase adjustments?",
        a: "Yes. If a client's intake includes cycle phase information, the compiler applies menstrual-cycle-aware nutrition and training patterns where the evidence supports it. Sarah, our nutrition-focus persona, demonstrates this. Cycle phase is optional — not all clients track it.",
      },
      {
        q: "Can a coach add custom constraints outside the standard list?",
        a: "The intake includes an 'other' constraint category with a free-text detail field. The compiler uses this field for context notes in the prescription output. Custom constraints do not match against the atom library the same way typed constraints do — that matching is limited to the set the library was indexed against.",
      },
    ],
  },
  {
    category: "Using the tool",
    items: [
      {
        q: "Do I need a biology or nutrition background to use this?",
        a: "You need enough background to evaluate what the plan surfaces and make professional decisions. The compiler handles citation retrieval and evidence ranking; the coach applies judgment to dosing, sequencing, and client readiness. If you are an independent health coach, RD, or strength coach, the tool is designed for your level of expertise.",
      },
      {
        q: "Can I use a plan as a client deliverable as-is?",
        a: "The raw plan is written for a coach-level reader — it includes constraint notes, population-specific parameterizations, and citation identifiers. For client-facing use, most coaches export the Markdown and strip or adapt the technical context before sharing. The PDF export is cleaner and prints well.",
      },
      {
        q: "Can I run multiple clients through the compiler?",
        a: "Yes. Each client gets a separate intake and a separate plan. Your dashboard lists all clients with their most recent plan and a compile status.",
      },
    ],
  },
  {
    category: "Pricing and beta",
    items: [
      {
        q: "What does 'free during beta' mean?",
        a: "During closed beta, the compiler is free for all coaches who sign up. We are still calibrating pricing based on real usage patterns. When billing launches, we will give existing beta users advance notice and a grandfathered rate.",
      },
      {
        q: "What will pricing look like after beta?",
        a: "We are planning a monthly subscription for active coaches with unlimited compiles, and per-pack credits for lower-volume use. See the pricing page for current thinking — it will update as we finalize the numbers.",
      },
      {
        q: "Is there a free tier after launch?",
        a: "We have not decided. A limited free tier (e.g., one compile per month) is possible. The goal is a price point that matches what independent coaches earn per client session.",
      },
    ],
  },
] as const;

export default function FAQPage() {
  return (
    <div className="mx-auto max-w-4xl px-6 py-20">
      {/* Header */}
      <div className="mb-14">
        <p className="mb-3 text-[0.68rem] font-semibold uppercase tracking-[0.2em] text-zinc-500">
          Common questions
        </p>
        <h1 className="mb-4 text-[2.2rem] font-semibold tracking-tight text-white">
          Frequently asked questions
        </h1>
        <p className="text-[0.88rem] leading-relaxed text-zinc-400">
          Can't find an answer?{" "}
          <a
            href="mailto:hello@hccompiler.com"
            className="text-zinc-200 underline underline-offset-2 hover:text-white"
          >
            Email us
          </a>
          .
        </p>
      </div>

      {/* FAQ groups */}
      <div className="flex flex-col gap-14">
        {FAQS.map(({ category, items }) => (
          <div key={category}>
            <p className="mb-6 text-[0.68rem] font-semibold uppercase tracking-[0.2em] text-zinc-500">
              {category}
            </p>
            <div className="flex flex-col divide-y divide-white/[0.05]">
              {items.map(({ q, a }) => (
                <div key={q} className="py-6">
                  <p className="mb-2 text-[0.88rem] font-semibold text-white">
                    {q}
                  </p>
                  <p className="text-[0.8rem] leading-relaxed text-zinc-400">
                    {a}
                  </p>
                </div>
              ))}
            </div>
          </div>
        ))}
      </div>

      {/* CTA */}
      <div className="mt-16 flex flex-wrap items-center gap-4 border-t border-white/[0.06] pt-10">
        <Link
          href="/sign-in"
          className="rounded-md bg-emerald-500 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-emerald-400"
        >
          Sign up — free during beta
        </Link>
        <Link
          href="/how-it-works"
          className="text-[0.78rem] text-zinc-400 underline underline-offset-2 hover:text-white"
        >
          How it works
        </Link>
      </div>
    </div>
  );
}
