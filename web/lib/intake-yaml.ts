// TS mirror of src/hcc_compiler/sp2/intake.py — keep in sync.
// Validation is permissive on the form side; backend pydantic is authoritative.

import yaml from "js-yaml";

export type Sex = "M" | "F" | "other";
export type TrainingStatus = "untrained" | "recreational" | "trained" | "competitive";
export type Goal =
  | "hypertrophy"
  | "strength"
  | "endurance"
  | "weight_loss"
  | "recomposition"
  | "performance"
  | "longevity";

export const ALL_GOALS: Goal[] = [
  "hypertrophy",
  "strength",
  "endurance",
  "weight_loss",
  "recomposition",
  "performance",
  "longevity",
];

export const ALL_TRAINING_STATUS: TrainingStatus[] = [
  "untrained",
  "recreational",
  "trained",
  "competitive",
];

export const ALL_SEX: Sex[] = ["M", "F", "other"];

export const CONSTRAINT_TYPES = [
  "injury",
  "dietary",
  "schedule",
  "equipment",
  "lifestyle",
  "other",
] as const;
export type ConstraintType = (typeof CONSTRAINT_TYPES)[number];

export interface Demographics {
  age: number;
  sex: Sex;
  weight_kg: number;
  height_cm: number;
}

export interface Constraint {
  type: ConstraintType | string;
  detail: string;
}

export interface ClientIntake {
  client_id: string;
  library_version: string;
  demographics: Demographics;
  training_status: TrainingStatus;
  goals: Goal[];
  current_regimen: string;
  constraints: Constraint[];
  contraindications: string[];
  metabolic_calibration: number | null;
}

export interface IntakeValidationError {
  field: string;
  message: string;
}

export function validateIntake(intake: ClientIntake): IntakeValidationError[] {
  const errs: IntakeValidationError[] = [];
  if (!intake.client_id.trim()) errs.push({ field: "client_id", message: "Required." });
  if (!intake.library_version.trim())
    errs.push({ field: "library_version", message: "Required (e.g. 0.2.0)." });
  if (intake.demographics.age < 14 || intake.demographics.age > 100)
    errs.push({ field: "demographics.age", message: "Must be 14–100." });
  if (intake.demographics.weight_kg <= 0 || intake.demographics.weight_kg > 300)
    errs.push({ field: "demographics.weight_kg", message: "Must be 0–300 kg." });
  if (intake.demographics.height_cm <= 0 || intake.demographics.height_cm > 250)
    errs.push({ field: "demographics.height_cm", message: "Must be 0–250 cm." });
  if (intake.goals.length < 1) errs.push({ field: "goals", message: "Pick at least one goal." });
  if (intake.current_regimen.length > 2000)
    errs.push({ field: "current_regimen", message: "Max 2000 chars." });
  if (
    intake.metabolic_calibration != null &&
    (intake.metabolic_calibration < 0.5 || intake.metabolic_calibration > 1.5)
  ) {
    errs.push({
      field: "metabolic_calibration",
      message: "Must be between 0.5 and 1.5, or leave blank.",
    });
  }
  return errs;
}

export function intakeToYaml(intake: ClientIntake): string {
  // Match the field order pydantic uses for stability across diffs.
  const ordered: Record<string, unknown> = {
    client_id: intake.client_id,
    library_version: intake.library_version,
    demographics: {
      age: intake.demographics.age,
      sex: intake.demographics.sex,
      weight_kg: intake.demographics.weight_kg,
      height_cm: intake.demographics.height_cm,
    },
    training_status: intake.training_status,
    goals: intake.goals,
    current_regimen: intake.current_regimen,
    constraints: intake.constraints.map((c) => ({ type: c.type, detail: c.detail })),
    contraindications: intake.contraindications,
  };
  if (intake.metabolic_calibration != null) {
    ordered.metabolic_calibration = intake.metabolic_calibration;
  }
  return yaml.dump(ordered, { lineWidth: 100, noRefs: true });
}

export function blankIntake(): ClientIntake {
  return {
    client_id: "",
    library_version: "0.2.0",
    demographics: { age: 30, sex: "M", weight_kg: 75, height_cm: 175 },
    training_status: "trained",
    goals: [],
    current_regimen: "",
    constraints: [],
    contraindications: [],
    metabolic_calibration: null,
  };
}
