// Local smoke for the LLM schedule generator.
// Run: cd web && ANTHROPIC_AUTH_TOKEN="$(zsvault get zai_api_key)" pnpm exec tsx scripts/smoke-schedule.ts <persona>
//
// Loads a persona's pack + intake from disk (no DB), generates a schedule,
// prints the validated result. Defaults to Z.AI GLM-4.6 — override with
// ANTHROPIC_BASE_URL / SCHEDULE_MODEL env vars.
import { promises as fs } from "node:fs";
import path from "node:path";
import yaml from "js-yaml";
import { generateSchedule } from "../lib/schedule/generate";
import type { ClientIntake, EvidencePack } from "../lib/data/types";

const PERSONAS: Record<string, { pack: string; intake: string }> = {
  carl: { pack: "carl.json", intake: "intake_carl_strength.yaml" },
  amy: { pack: "amy.json", intake: "intake_amy_runner.yaml" },
  tori: { pack: "test_v2_tori_shaw.json", intake: "intake_test_v2_tori_shaw.yaml" },
};

async function main() {
  const slug = process.argv[2] ?? "carl";
  const cfg = PERSONAS[slug];
  if (!cfg) {
    console.error(`Unknown persona '${slug}'. Available: ${Object.keys(PERSONAS).join(", ")}`);
    process.exit(2);
  }

  const repoRoot = path.resolve(__dirname, "..", "..");
  const packPath = path.join(repoRoot, "docs", "examples", "sp2", cfg.pack);
  const intakePath = path.join(repoRoot, "tests", "fixtures", "intakes", cfg.intake);

  const [packRaw, intakeRaw] = await Promise.all([
    fs.readFile(packPath, "utf-8"),
    fs.readFile(intakePath, "utf-8"),
  ]);
  const pack = JSON.parse(packRaw) as EvidencePack;
  const intake = yaml.load(intakeRaw) as ClientIntake;

  console.error(`[smoke] persona=${slug} pack=${packPath} intake=${intakePath}`);
  console.error(`[smoke] calling Claude via ${process.env.ANTHROPIC_BASE_URL}...`);

  const t0 = Date.now();
  const schedule = await generateSchedule(intake, pack);
  const elapsed = Date.now() - t0;

  console.error(`[smoke] OK in ${elapsed}ms`);
  console.log(JSON.stringify(schedule, null, 2));
}

main().catch((e) => {
  console.error("[smoke] FAIL:", e instanceof Error ? e.stack : e);
  process.exit(1);
});
