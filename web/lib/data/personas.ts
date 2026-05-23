/**
 * The 9 personas the viewer can navigate. Slug = URL segment.
 * packFile + intakeFile point at on-disk artifacts; full paths are resolved
 * in `loader.ts` relative to the compiler repo root.
 */

export interface Persona {
  slug: string;
  displayName: string;
  initials: string;
  packFile: string;        // under docs/examples/sp2/
  intakeFile: string;      // under tests/fixtures/intakes/
  tagline: string;         // short context line under the name
}

export const PERSONAS: Persona[] = [
  {
    slug: "amy",
    displayName: "Amy",
    initials: "AM",
    packFile: "amy.json",
    intakeFile: "intake_amy_runner.yaml",
    tagline: "Recreational runner · endurance focus",
  },
  {
    slug: "carl",
    displayName: "Carl",
    initials: "CL",
    packFile: "carl.json",
    intakeFile: "intake_carl_strength.yaml",
    tagline: "Strength athlete · renal-flagged",
  },
  {
    slug: "sam",
    displayName: "Sam",
    initials: "SM",
    packFile: "sam.json",
    intakeFile: "intake_sam_recomp.yaml",
    tagline: "Recomposition · trained",
  },
  {
    slug: "bradley",
    displayName: "Bradley",
    initials: "BR",
    packFile: "test_v2_bradley.json",
    intakeFile: "intake_test_v2_bradley.yaml",
    tagline: "Boxing · low-back rehab",
  },
  {
    slug: "david",
    displayName: "David",
    initials: "DV",
    packFile: "test_v2_david.json",
    intakeFile: "intake_test_v2_david.yaml",
    tagline: "Executive · 22% metabolic inefficiency",
  },
  {
    slug: "jackson",
    displayName: "Jackson",
    initials: "JW",
    packFile: "test_v2_jackson_white.json",
    intakeFile: "intake_test_v2_jackson_white.yaml",
    tagline: "Post-fusion · machine-only",
  },
  {
    slug: "sarah",
    displayName: "Sarah",
    initials: "SN",
    packFile: "test_v2_sarah_nutrition.json",
    intakeFile: "intake_test_v2_sarah_nutrition.yaml",
    tagline: "Cycle-aware · nutrition focus",
  },
  {
    slug: "sebastian",
    displayName: "Sebastian",
    initials: "SB",
    packFile: "test_v2_sebastian.json",
    intakeFile: "intake_test_v2_sebastian.yaml",
    tagline: "NDT · longevity track",
  },
  {
    slug: "tori",
    displayName: "Tori",
    initials: "TS",
    packFile: "test_v2_tori_shaw.json",
    intakeFile: "intake_test_v2_tori_shaw.yaml",
    tagline: "MASLD · hypothyroidism",
  },
];

export const DEFAULT_PERSONA_SLUG = "carl";

export function getPersona(slug: string): Persona | null {
  return PERSONAS.find((p) => p.slug === slug) ?? null;
}
