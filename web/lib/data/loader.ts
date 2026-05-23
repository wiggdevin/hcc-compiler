import { promises as fs } from "node:fs";
import path from "node:path";
import yaml from "js-yaml";
import { cache } from "react";
import type { EvidencePack, ClientIntake } from "./types";
import { getPersona } from "./personas";

/**
 * Web app lives at <repo>/web/. Compiler artifacts live at:
 *   <repo>/docs/examples/sp2/<pack>.json
 *   <repo>/tests/fixtures/intakes/<intake>.yaml
 */
const REPO_ROOT = path.resolve(process.cwd(), "..");
const PACK_DIR = path.join(REPO_ROOT, "docs", "examples", "sp2");
const INTAKE_DIR = path.join(REPO_ROOT, "tests", "fixtures", "intakes");

export const loadEvidencePack = cache(
  async (slug: string): Promise<EvidencePack> => {
    const persona = getPersona(slug);
    if (!persona) {
      throw new Error(`Unknown persona slug: ${slug}`);
    }
    const file = path.join(PACK_DIR, persona.packFile);
    const raw = await fs.readFile(file, "utf-8");
    return JSON.parse(raw) as EvidencePack;
  },
);

export const loadIntake = cache(
  async (slug: string): Promise<ClientIntake> => {
    const persona = getPersona(slug);
    if (!persona) {
      throw new Error(`Unknown persona slug: ${slug}`);
    }
    const file = path.join(INTAKE_DIR, persona.intakeFile);
    const raw = await fs.readFile(file, "utf-8");
    return yaml.load(raw) as ClientIntake;
  },
);
