import type { LucideIcon } from "lucide-react";
import {
  Apple,
  Dumbbell,
  HeartPulse,
  Pill,
  BedDouble,
  Brain,
} from "lucide-react";
import type { Domain } from "./types";

export interface DomainMeta {
  id: Domain;
  label: string;
  shortLabel: string;
  icon: LucideIcon;
  /** route hash for cross-page anchors, e.g. /clients/carl/recovery#supplements */
  routeHash?: string;
  /** Which top-nav page hosts this domain. */
  hostRoute: "diet" | "workout" | "recovery";
}

export const DOMAIN_META: Record<Domain, DomainMeta> = {
  nutrition: {
    id: "nutrition",
    label: "Nutrition",
    shortLabel: "Nutrition",
    icon: Apple,
    hostRoute: "diet",
  },
  training: {
    id: "training",
    label: "Training",
    shortLabel: "Training",
    icon: Dumbbell,
    hostRoute: "workout",
  },
  conditioning: {
    id: "conditioning",
    label: "Conditioning",
    shortLabel: "Cardio",
    icon: HeartPulse,
    hostRoute: "workout",
    routeHash: "conditioning",
  },
  supplements: {
    id: "supplements",
    label: "Supplements",
    shortLabel: "Supplements",
    icon: Pill,
    hostRoute: "recovery",
    routeHash: "supplements",
  },
  recovery: {
    id: "recovery",
    label: "Recovery",
    shortLabel: "Recovery",
    icon: BedDouble,
    hostRoute: "recovery",
  },
  behavioral: {
    id: "behavioral",
    label: "Behavioral",
    shortLabel: "Behavior",
    icon: Brain,
    hostRoute: "recovery",
    routeHash: "behavioral",
  },
};

export const DOMAIN_ORDER: Domain[] = [
  "nutrition",
  "training",
  "conditioning",
  "supplements",
  "recovery",
  "behavioral",
];
