// LLM schedule generator. Calls an Anthropic-compatible API via plain stdlib
// fetch — no SDK, no pay-per-token. Subscription-only per project rules.
//
// Default routing: Z.AI's anthropic-compatible endpoint with GLM-4.6
// (Z.AI GLM Coding Max subscription). The zs-anthropic-proxy alternative
// (claude-sonnet via user's Claude Max) was tested empirically and times out
// at 5 min on prompts >2k tokens — Claude Max queues throttle the proxy.
//
// Env vars expected:
//   ANTHROPIC_BASE_URL   default: https://api.z.ai/api/anthropic
//   ANTHROPIC_AUTH_TOKEN required (zsvault: zai_api_key)
//   SCHEDULE_MODEL       default: glm-4.6
//
// The pack is rendered as a slim markdown brief (~2.5k tokens) — large JSON
// dumps cause empty/refusal responses across both providers.

import type { ClientIntake, EvidencePack } from "@/lib/data/types";
import { validateSchedule, type Schedule } from "./types";

const MODEL = process.env.SCHEDULE_MODEL ?? "glm-4.6";
const BASE_URL =
  process.env.ANTHROPIC_BASE_URL ?? "https://api.z.ai/api/anthropic";
const MAX_TOKENS = 8192;
const TEMPERATURE = 0.4;

interface AnthropicMessageContent {
  type: string;
  text?: string;
}
interface AnthropicMessageResponse {
  content: AnthropicMessageContent[];
  stop_reason?: string;
}

const SYSTEM_PROMPT = `You translate an evidence-backed health plan into a 7-day program a client can follow.

Voice: a great coach speaking to their client. Concrete, kind, direct. Specific food suggestions ("3 eggs + 60g oats + a handful of blueberries"), not generic categories. Plain-English rationale ("protein right after lifting helps muscles rebuild") — not literature citations.

Respect intake constraints. If the brief lists a contraindication, allergy, or schedule cap (45-min limit, intermittent fasting window, post-injury), reflect it in every day.

The backing_atom_ids field is the only place where EA-* / RP-* IDs may appear (those go into the Why tab's expandable cards in the UI).

Output a single JSON object matching this exact schema. JSON only — no prose before or after, no markdown commentary:

{
  "weekly_focus": "1-2 sentence focus for the week",
  "days": [
    {
      "day": "Mon",
      "training": {
        "title": "Lower body strength",
        "items": [{"name": "Back squat", "sets": 4, "reps": "6-8", "notes": "Optional brace"}],
        "duration_min": 50
      },
      "nutrition": {
        "protein_target_g": 145,
        "meals": [
          {"meal": "Breakfast", "suggestion": "5 eggs + 60g oats + berries", "macros": {"p": 45, "c": 60, "f": 15}}
        ]
      },
      "recovery": ["7-9h sleep", "10-min walk after dinner"]
    }
  ],
  "supplements": [
    {"name": "Creatine monohydrate", "dose": "5g", "timing": "with first meal", "why_plain": "Helps muscles work harder for longer in training."}
  ],
  "recommendations": [
    {"headline": "Eat protein evenly across 4 meals", "why_plain": "Spreads out muscle-building stimulus through the day.", "backing_atom_ids": ["EA-NUT-1234"]}
  ]
}

Rules:
- days array must be exactly 7 entries Mon→Sun in that order.
- training may be null on rest days.
- 5-8 supplements maximum (skip if the plan doesn't recommend any).
- 6-12 recommendations for the Why tab.`;

function fmtConstraints(intake: ClientIntake): string {
  const constraints = (intake.constraints ?? [])
    .map((c) => `- ${c.type}: ${c.detail}`)
    .join("\n");
  const contras = (intake.contraindications ?? [])
    .map((s) => `- ${s}`)
    .join("\n");
  return [
    constraints ? `### Constraints\n${constraints}` : "",
    contras ? `### Contraindications\n${contras}` : "",
  ]
    .filter(Boolean)
    .join("\n\n");
}

function fmtDemographics(intake: ClientIntake): string {
  const dem = (intake.demographics ?? {}) as unknown as Record<string, unknown>;
  const parts: string[] = [];
  if (dem.age) parts.push(`age ${dem.age}`);
  if (dem.sex) parts.push(`${dem.sex}`);
  if (dem.weight_kg) parts.push(`${dem.weight_kg}kg`);
  if (dem.height_cm) parts.push(`${dem.height_cm}cm`);
  return parts.join(", ");
}

function renderIntakeBrief(intake: ClientIntake): string {
  const goals = (intake.goals ?? []).map((g) => `- ${g}`).join("\n");
  const regimen = intake.current_regimen?.trim();
  return [
    `## Client brief`,
    `**Identity:** ${intake.client_id} — ${fmtDemographics(intake)}`,
    intake.training_status ? `**Training status:** ${intake.training_status}` : "",
    goals ? `### Goals\n${goals}` : "",
    regimen ? `### Current regimen\n${regimen}` : "",
    fmtConstraints(intake),
  ]
    .filter(Boolean)
    .join("\n\n");
}

function truncate(text: string, n: number): string {
  if (text.length <= n) return text;
  return text.slice(0, n).trimEnd() + "…";
}

function renderPackBrief(pack: EvidencePack): string {
  const lines: string[] = ["## Evidence-backed recommendations"];
  for (const [domain, block] of Object.entries(
    pack.domain_recommendations ?? {},
  )) {
    if (!block) continue;
    const patterns = block.patterns ?? [];
    const atoms = block.atoms ?? [];
    if (!patterns.length && !atoms.length) continue;
    lines.push(`\n### ${domain.toUpperCase()}`);
    for (const p of patterns.slice(0, 2)) {
      lines.push(`- **${p.pattern_id}** — ${truncate(p.applies_because, 220)}`);
      if (p.parameterization)
        lines.push(`  - How to apply: ${truncate(p.parameterization, 260)}`);
    }
    for (const a of atoms.slice(0, 4)) {
      lines.push(`- \`${a.atom_id}\` — ${truncate(a.claim, 200)}`);
    }
  }
  const preempt = pack.compile_metadata?.preemptive_contraindications ?? [];
  if (preempt.length) {
    lines.push(`\n### Safety preflight (HARD constraints — respect every day)`);
    for (const p of preempt.slice(0, 6)) {
      const rec = p as { matched_needle?: string; claim_or_summary?: string };
      const what = rec.claim_or_summary ?? "";
      const why = rec.matched_needle ?? "";
      lines.push(`- ${truncate(what, 160)} — ${truncate(why, 100)}`);
    }
  }
  return lines.join("\n");
}

function buildUserPrompt(intake: ClientIntake, pack: EvidencePack): string {
  return [
    renderIntakeBrief(intake),
    "",
    renderPackBrief(pack),
    "",
    "Produce the 7-day Schedule JSON now (Mon→Sun). JSON only — no commentary.",
  ].join("\n");
}

function extractJson(text: string): unknown {
  const fence = text.match(/```(?:json)?\s*([\s\S]*?)```/);
  const candidate = (fence ? fence[1] : text).trim();
  const start = candidate.indexOf("{");
  const end = candidate.lastIndexOf("}");
  if (start === -1 || end === -1 || end <= start) {
    throw new Error("no JSON object found in model response");
  }
  return JSON.parse(candidate.slice(start, end + 1));
}

async function callLLM(userPrompt: string): Promise<string> {
  const token = process.env.ANTHROPIC_AUTH_TOKEN ?? "";
  if (!token) {
    throw new Error("ANTHROPIC_AUTH_TOKEN not set");
  }

  const url = `${BASE_URL.replace(/\/$/, "")}/v1/messages`;
  const body = {
    model: MODEL,
    max_tokens: MAX_TOKENS,
    temperature: TEMPERATURE,
    system: SYSTEM_PROMPT,
    messages: [{ role: "user", content: userPrompt }],
  };

  const res = await fetch(url, {
    method: "POST",
    headers: {
      "content-type": "application/json",
      "x-api-key": token,
      "anthropic-version": "2023-06-01",
    },
    body: JSON.stringify(body),
  });

  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`LLM ${res.status}: ${errText.slice(0, 400)}`);
  }

  const data = (await res.json()) as AnthropicMessageResponse;
  const text = data.content
    ?.filter((c) => c.type === "text" && typeof c.text === "string")
    .map((c) => c.text)
    .join("\n")
    .trim();
  if (!text) {
    throw new Error(
      `LLM returned empty response (stop_reason=${data.stop_reason ?? "?"}, content=${JSON.stringify(data.content).slice(0, 400)})`,
    );
  }
  return text;
}

export async function generateSchedule(
  intake: ClientIntake,
  pack: EvidencePack,
): Promise<Schedule> {
  const userPrompt = buildUserPrompt(intake, pack);
  let lastErr: string | null = null;

  for (let attempt = 0; attempt < 2; attempt++) {
    const tighter =
      attempt === 1
        ? `\n\n(Retry — previous output was invalid: ${lastErr ?? "unknown"}. Output the JSON object only, no markdown fence, no prose. days array MUST be exactly 7 entries in Mon→Sun order.)`
        : "";
    const text = await callLLM(userPrompt + tighter);
    try {
      const parsed = extractJson(text);
      const validated = validateSchedule(parsed);
      if ("error" in validated) {
        lastErr = validated.error;
        continue;
      }
      return validated;
    } catch (e) {
      lastErr = e instanceof Error ? e.message : String(e);
      continue;
    }
  }

  throw new Error(`Schedule generation failed: ${lastErr ?? "unknown"}`);
}
