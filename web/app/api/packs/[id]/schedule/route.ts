// POST /api/packs/:id/schedule — generate or fetch cached Schedule.
// GET  /api/packs/:id/schedule — fetch cached only (404 if not generated).
//
// Authenticated coach must own the pack. Service role bypasses RLS for the
// actual read/write once auth check passes.

import { NextResponse } from "next/server";
import { requireCoach } from "@/lib/auth";
import { createAdminClient } from "@/lib/supabase/admin";
import { getOrGenerateSchedule, loadCachedSchedule } from "@/lib/schedule/load";
import type { ClientIntake, EvidencePack } from "@/lib/data/types";

interface PackRow {
  id: string;
  intake_id: string;
  coach_id: string;
  json_path: string;
}
interface IntakeRow {
  payload: ClientIntake;
}

async function loadPackAndIntake(
  packId: string,
  coachId: string,
): Promise<{ pack: EvidencePack; intake: ClientIntake } | null> {
  const admin = createAdminClient();
  const { data: packRow } = await admin
    .from("packs")
    .select("id, intake_id, coach_id, json_path")
    .eq("id", packId)
    .eq("coach_id", coachId)
    .maybeSingle<PackRow>();
  if (!packRow) return null;

  const { data: intakeRow } = await admin
    .from("intakes")
    .select("payload")
    .eq("id", packRow.intake_id)
    .maybeSingle<IntakeRow>();
  if (!intakeRow) return null;

  const { data: blob, error } = await admin.storage
    .from("packs")
    .download(packRow.json_path);
  if (error || !blob) return null;

  const pack = JSON.parse(await blob.text()) as EvidencePack;
  return { pack, intake: intakeRow.payload };
}

export async function GET(
  _req: Request,
  ctx: { params: Promise<{ id: string }> },
) {
  const coach = await requireCoach();
  const { id: packId } = await ctx.params;

  // Auth: confirm coach owns the pack before exposing the cached schedule.
  const admin = createAdminClient();
  const { data: owned } = await admin
    .from("packs")
    .select("id")
    .eq("id", packId)
    .eq("coach_id", coach.id)
    .maybeSingle();
  if (!owned) {
    return NextResponse.json({ error: "not found" }, { status: 404 });
  }

  const schedule = await loadCachedSchedule(packId);
  if (!schedule) {
    return NextResponse.json({ error: "no cached schedule" }, { status: 404 });
  }
  return NextResponse.json(schedule);
}

export async function POST(
  _req: Request,
  ctx: { params: Promise<{ id: string }> },
) {
  const coach = await requireCoach();
  const { id: packId } = await ctx.params;

  const loaded = await loadPackAndIntake(packId, coach.id);
  if (!loaded) {
    return NextResponse.json({ error: "not found" }, { status: 404 });
  }

  try {
    const schedule = await getOrGenerateSchedule({
      packId,
      intake: loaded.intake,
      pack: loaded.pack,
    });
    return NextResponse.json(schedule);
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    console.error("[schedule POST] generation failed:", msg);
    return NextResponse.json(
      { error: "schedule generation failed", detail: msg },
      { status: 502 },
    );
  }
}
