import type { Metadata } from "next";
import Link from "next/link";

export const metadata: Metadata = {
  title: "How it works — HCC Compiler",
  description:
    "Walk through the three-step workflow from intake form to PDF-ready evidence-backed plan.",
};

export const dynamic = "force-static";

const STEPS = [
  {
    step: "01",
    heading: "Fill the intake form",
    body: [
      "The intake captures everything the compiler needs to make constraint-aware decisions: demographics (sex, age, weight, height, training status), primary goals as a multi-select, a typed constraint list (injury, dietary, schedule, and other — each with a detail field), contraindications, and current regimen.",
      "The form takes five minutes for a typical client. Every field maps to a validated schema so the compiler receives clean, structured data rather than free-form notes.",
    ],
    detail:
      "The intake schema mirrors a pydantic model — the web form is Zod-validated before the payload leaves the browser. Constraint types (injury, dietary, schedule, other) are typed enums, not text fields, so the safety preflight can pattern-match reliably.",
  },
  {
    step: "02",
    heading: "The compiler builds the evidence stack",
    body: [
      "Once the intake is submitted, the compiler runs against a 200+ atom evidence library. Each atom is a research claim tied to a specific population, dose range, and DOI-verified citation.",
      "A semantic similarity search ranks atoms and patterns by relevance to this client's goals and constraints. A two-layer citation gate discards anything that can't resolve to a real paper. Contraindications trigger a preflight that flags safety concerns inline — not as a final disclaimer, but at the prescription level where the coach needs to see them.",
    ],
    detail:
      "The citation gate runs at library harvest time (not per request), so by the time a plan reaches a coach, every backing reference has already been validated against PubMed and Crossref. Request-time is just ranking and rendering.",
  },
  {
    step: "03",
    heading: "Review, export, and coach",
    body: [
      "The plan viewer organizes prescriptions across six domains: nutrition, training, sleep, supplementation, recovery, and lifestyle. Each domain shows a confidence score, the evidence atoms and patterns that drove it, and inline constraint notes for this client.",
      "Export as Markdown for your notes software, or generate a PDF for the client-facing deliverable. Everything is labeled with the library version so you know exactly what build produced this plan.",
    ],
    detail:
      "PDF generation renders the same HTML that the plan viewer shows — no separate template to maintain. The print stylesheet strips navigation and expands all collapsibles so the coach gets a clean, readable document without layout surprises.",
  },
] as const;

const DETAILS = [
  {
    heading: "What is an 'atom'?",
    body: "An atom is a single evidence claim extracted from a peer-reviewed paper. It carries the claim text, the population it applies to (e.g., 'resistance-trained adults, 18–49y'), the recommended dose or range, the DOI, and a tier rating based on study design quality. Patterns are higher-level protocols that cite multiple atoms.",
  },
  {
    heading: "How does the confidence score work?",
    body: "Each domain's confidence score is a weighted average of the atoms and patterns that contributed to it, adjusted by citation tier (RCT > meta-analysis > observational). An overall plan confidence aggregates across all six domains. The score is not a quality rating of your coaching — it reflects how well the evidence library covers this client's specific combination of goals and constraints.",
  },
  {
    heading: "What does the safety preflight catch?",
    body: "Before generating prescriptions, the compiler checks every atom and pattern against the client's contraindications. If a creatine atom is matched for a client with documented renal insufficiency, that match is flagged — prominently, at the top of the plan — so the coach can decide whether to modify, defer, or skip that recommendation.",
  },
] as const;

export default function HowItWorksPage() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-20">
      {/* Header */}
      <div className="mb-16 max-w-2xl">
        <p className="mb-3 text-[0.68rem] font-semibold uppercase tracking-[0.2em] text-zinc-500">
          The workflow
        </p>
        <h1 className="mb-4 text-[2.2rem] font-semibold tracking-tight text-white">
          How HCC Compiler works
        </h1>
        <p className="text-[0.88rem] leading-relaxed text-zinc-400">
          Three steps from intake to a plan you can hand a client and defend.
          No black-box outputs, no hallucinated citations.
        </p>
      </div>

      {/* Steps */}
      <div className="flex flex-col gap-16">
        {STEPS.map(({ step, heading, body, detail }) => (
          <div
            key={step}
            className="grid gap-8 border-t border-white/[0.06] pt-12 lg:grid-cols-12"
          >
            <div className="lg:col-span-1">
              <span className="font-mono text-[0.65rem] font-medium tracking-widest text-emerald-400">
                {step}
              </span>
            </div>
            <div className="flex flex-col gap-4 lg:col-span-6">
              <h2 className="text-[1.2rem] font-semibold text-white">
                {heading}
              </h2>
              {body.map((paragraph, i) => (
                <p
                  key={i}
                  className="text-[0.82rem] leading-relaxed text-zinc-400"
                >
                  {paragraph}
                </p>
              ))}
            </div>
            <div className="rounded-lg border border-white/[0.07] bg-white/[0.02] p-5 lg:col-span-5">
              <p className="text-[0.72rem] leading-relaxed text-zinc-500">
                {detail}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Details section */}
      <div className="mt-24 border-t border-white/[0.06] pt-16">
        <h2 className="mb-10 text-[1.3rem] font-semibold text-white">
          Under the hood
        </h2>
        <div className="grid gap-6 sm:grid-cols-3">
          {DETAILS.map(({ heading, body }) => (
            <div
              key={heading}
              className="flex flex-col gap-3 rounded-xl border border-white/[0.07] bg-white/[0.02] p-6"
            >
              <h3 className="text-[0.85rem] font-semibold text-white">
                {heading}
              </h3>
              <p className="text-[0.76rem] leading-relaxed text-zinc-400">
                {body}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* CTA */}
      <div className="mt-20 flex flex-wrap items-center gap-4 border-t border-white/[0.06] pt-12">
        <Link
          href="/sign-in"
          className="rounded-md bg-emerald-500 px-5 py-2.5 text-sm font-medium text-white transition-colors hover:bg-emerald-400"
        >
          Try with a sample client
        </Link>
        <Link
          href="/samples/carl-sample-plan.md"
          prefetch={false}
          target="_blank"
          rel="noopener noreferrer"
          className="rounded-md border border-white/10 px-5 py-2.5 text-sm font-medium text-zinc-200 transition-colors hover:border-white/20 hover:text-white"
        >
          See a sample plan
        </Link>
        <Link
          href="/faq"
          className="text-[0.78rem] text-zinc-400 underline underline-offset-2 hover:text-white"
        >
          Read the FAQ
        </Link>
      </div>
    </div>
  );
}
