// Cache + load helpers for the Schedule.
//
// Storage path: `packs/schedule/{pack_id}.json` (same bucket as the
// EvidencePack JSON; key prefix scopes it). Cache miss = no object;
// cache hit = parsed Schedule.

import { createAdminClient } from "@/lib/supabase/admin";
import { generateSchedule } from "./generate";
import { validateSchedule, type Schedule } from "./types";
import type { ClientIntake, EvidencePack } from "@/lib/data/types";

const BUCKET = "packs";
const cacheKey = (packId: string): string => `schedule/${packId}.json`;

export async function loadCachedSchedule(
  packId: string,
): Promise<Schedule | null> {
  const admin = createAdminClient();
  const { data, error } = await admin.storage
    .from(BUCKET)
    .download(cacheKey(packId));
  if (error || !data) return null;
  try {
    const parsed = JSON.parse(await data.text()) as unknown;
    const validated = validateSchedule(parsed);
    if ("error" in validated) return null;
    return validated;
  } catch {
    return null;
  }
}

export async function getOrGenerateSchedule({
  packId,
  intake,
  pack,
}: {
  packId: string;
  intake: ClientIntake;
  pack: EvidencePack;
}): Promise<Schedule> {
  const cached = await loadCachedSchedule(packId);
  if (cached) return cached;

  const schedule = await generateSchedule(intake, pack);

  const admin = createAdminClient();
  const { error: uploadErr } = await admin.storage
    .from(BUCKET)
    .upload(cacheKey(packId), JSON.stringify(schedule, null, 2), {
      contentType: "application/json",
      upsert: true,
    });
  if (uploadErr) {
    // Non-fatal: return the generated schedule but log so coach retries can fix.
    console.error("[schedule] upload failed:", uploadErr.message);
  }
  return schedule;
}
