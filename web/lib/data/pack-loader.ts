// Unified pack loader for /clients/[id]/* routes.
//
// Two modes selected by [id] format:
//   - Persona slug ("carl", "tori", …) → loads on-disk demo pack, no auth
//   - UUID                              → loads coach-owned pack from
//                                        Supabase Storage; requires the
//                                        signed-in coach to own the pack.
//
// Pages call `loadPackForView(id)` and render whatever it returns. The
// function throws `notFound()` (Next.js) when the slug is unknown or the
// coach is not authorized.

import { promises as fs } from "node:fs";
import path from "node:path";
import { notFound } from "next/navigation";
import yaml from "js-yaml";
import { cache } from "react";
import { createClient as createServerClient } from "@/lib/supabase/server";
import { createAdminClient } from "@/lib/supabase/admin";
import { getPersona, type Persona } from "./personas";
import type { EvidencePack, ClientIntake } from "./types";

// The 9 demo personas are bundled into web/public/{sp2,intakes}/ at build
// time (see web/package.json `prebuild` script) so they ship with the
// deployed Vercel function. `process.cwd()` is the web/ root in both dev
// and production serverless contexts.
const PACK_DIR = path.join(process.cwd(), "public", "sp2");
const INTAKE_DIR = path.join(process.cwd(), "public", "intakes");

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export interface PackView {
  /** Synthesized for coach packs so Header/PersonaSwitcher can render unchanged. */
  persona: Persona;
  /** The compiled evidence pack JSON. */
  pack: EvidencePack;
  /** The original intake (for the /intake tab + breadcrumbs). */
  intake: ClientIntake;
  /** "persona" or "coach" — pages may render differently per source. */
  source: "persona" | "coach";
}

export const loadPackForView = cache(async (id: string): Promise<PackView> => {
  if (UUID_RE.test(id)) {
    return loadCoachPack(id);
  }
  return loadPersonaPack(id);
});

async function loadPersonaPack(slug: string): Promise<PackView> {
  const persona = getPersona(slug);
  if (!persona) notFound();

  const packFile = path.join(PACK_DIR, persona.packFile);
  const intakeFile = path.join(INTAKE_DIR, persona.intakeFile);
  const [packRaw, intakeRaw] = await Promise.all([
    fs.readFile(packFile, "utf-8"),
    fs.readFile(intakeFile, "utf-8"),
  ]);

  return {
    persona,
    pack: JSON.parse(packRaw) as EvidencePack,
    intake: yaml.load(intakeRaw) as ClientIntake,
    source: "persona",
  };
}

async function loadCoachPack(packId: string): Promise<PackView> {
  // Auth: the signed-in coach must own this pack.
  const supabase = await createServerClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();
  if (!user) notFound();

  const { data: row } = await supabase
    .from("packs")
    .select("id, coach_id, intake_id, json_path")
    .eq("id", packId)
    .eq("coach_id", user.id)
    .maybeSingle();

  if (!row) notFound();

  // Pull intake payload (the original ClientIntake).
  const { data: intakeRow } = await supabase
    .from("intakes")
    .select("payload, client_id")
    .eq("id", row.intake_id)
    .maybeSingle();

  if (!intakeRow) notFound();

  // Download the compiled JSON from Storage. Service-role bypasses RLS on
  // storage.objects but we've already verified ownership above.
  const admin = createAdminClient();
  const { data: blob, error: dlError } = await admin.storage
    .from("packs")
    .download(row.json_path);

  if (dlError || !blob) notFound();

  const packJson = JSON.parse(await blob.text()) as EvidencePack;

  // Synthesize a Persona so the existing Header/PersonaSwitcher renders.
  const displayName = intakeRow.client_id ?? "Client";
  const persona: Persona = {
    slug: packId,
    displayName,
    initials: displayName.slice(0, 2).toUpperCase(),
    packFile: "",
    intakeFile: "",
    tagline: "Coach-compiled plan",
  };

  return {
    persona,
    pack: packJson,
    intake: intakeRow.payload as ClientIntake,
    source: "coach",
  };
}
