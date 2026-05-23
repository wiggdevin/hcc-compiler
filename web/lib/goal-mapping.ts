import type { EvidencePack, PatternMatch } from "./data/types";

/**
 * Heuristic keyword map. Keys cover both the canonical `Goal` union values
 * (e.g. "hypertrophy", "weight_loss") AND common intake free-text variants
 * (e.g. "fat_loss", "build_strength") since intake.goals[] is loose in
 * practice. Unknown goals → empty list → no matches.
 */
const GOAL_KEYWORDS: Record<string, string[]> = {
  hypertrophy: ["hypertrophy", "muscle", "lean mass", "lean-mass"],
  strength: ["resistance", "strength", "hypertrophy", "muscle"],
  build_strength: ["resistance", "strength", "hypertrophy", "muscle"],
  endurance: ["endurance", "aerobic", "vo2", "cardio"],
  weight_loss: ["fat", "deficit", "weight loss", "weight-loss"],
  fat_loss: ["fat", "deficit", "weight loss", "weight-loss"],
  recomposition: [
    "recomp",
    "lean mass",
    "lean-mass",
    "fat",
    "deficit",
    "hypertrophy",
  ],
  performance: ["performance", "power", "output", "speed"],
  longevity: ["longevity", "healthspan", "aging", "older"],
  improve_recovery: ["recovery", "sleep", "stress"],
  recovery: ["recovery", "sleep", "stress"],
  sleep: ["sleep", "circadian"],
};

function keywordsFor(goal: string): string[] {
  return GOAL_KEYWORDS[goal] ?? [];
}

function formatGoalLabel(goal: string): string {
  return goal.replace(/_/g, " ");
}

function patternMatchesGoal(pattern: PatternMatch, goal: string): boolean {
  const keywords = keywordsFor(goal);
  if (keywords.length === 0) return false;
  const hay = pattern.applies_because.toLowerCase();
  return keywords.some((kw) => hay.includes(kw));
}

/**
 * For each goal, return the patterns across all domains whose
 * `applies_because` text matches the goal's keyword list. Key = original
 * goal string (not display-formatted); value = matching patterns.
 */
export function mapGoalsToPatterns(
  goals: string[],
  pack: EvidencePack,
): Map<string, PatternMatch[]> {
  const out = new Map<string, PatternMatch[]>();
  const allPatterns: PatternMatch[] = Object.values(
    pack.domain_recommendations,
  ).flatMap((b) => b.patterns);

  for (const goal of goals) {
    const matches = allPatterns.filter((p) => patternMatchesGoal(p, goal));
    out.set(goal, matches);
  }
  return out;
}

/**
 * Given a single pattern and the client's goals, return the display-formatted
 * goals that this pattern targets. Used for the small "Targets: X · Y" chip.
 */
export function targetedGoalsForPattern(
  pattern: PatternMatch,
  goals: string[],
): string[] {
  return goals
    .filter((g) => patternMatchesGoal(pattern, g))
    .map(formatGoalLabel);
}
