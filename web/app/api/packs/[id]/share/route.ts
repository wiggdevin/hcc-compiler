// POST /api/packs/:id/share — mint share token + generate schedule + email client.
//
// Body: { clientEmail: string, clientFirstName?: string, customMessage?: string, customSubject?: string }
//
// Steps:
//   1. Auth: coach must own the pack.
//   2. Generate (or fetch cached) Schedule.
//   3. Insert share_tokens row (owner = coach, pack_id = :id).
//   4. Send branded email via Resend → /p/<token>.
//   5. Update share_tokens.sent_at on success.

import { NextResponse } from "next/server";
import { requireCoach } from "@/lib/auth";
import { createAdminClient } from "@/lib/supabase/admin";
import { getOrGenerateSchedule } from "@/lib/schedule/load";
import { sendPlanReadyForClientEmail } from "@/lib/resend";
import type { ClientIntake, EvidencePack } from "@/lib/data/types";

interface PackRow {
  id: string;
  intake_id: string;
  coach_id: string;
  json_path: string;
}
interface IntakeRow {
  payload: ClientIntake;
  client_id: string;
}
interface CoachRow {
  display_name: string | null;
  headshot_url: string | null;
}

async function loadCoachPackContext(packId: string, coachId: string) {
  const admin = createAdminClient();
  const { data: packRow } = await admin
    .from("packs")
    .select("id, intake_id, coach_id, json_path")
    .eq("id", packId)
    .eq("coach_id", coachId)
    .maybeSingle<PackRow>();
  if (!packRow) return null;

  const [{ data: intakeRow }, { data: coachRow }, { data: blob, error: dlErr }] =
    await Promise.all([
      admin
        .from("intakes")
        .select("payload, client_id")
        .eq("id", packRow.intake_id)
        .maybeSingle<IntakeRow>(),
      admin
        .from("coaches")
        .select("display_name, headshot_url")
        .eq("id", coachId)
        .maybeSingle<CoachRow>(),
      admin.storage.from("packs").download(packRow.json_path),
    ]);
  if (!intakeRow || !coachRow || dlErr || !blob) return null;

  const pack = JSON.parse(await blob.text()) as EvidencePack;
  return { packRow, intakeRow, coachRow, pack };
}

function appBaseUrl(): string {
  return (
    process.env.NEXT_PUBLIC_APP_URL ??
    process.env.VERCEL_PROJECT_PRODUCTION_URL_PREFIX ??
    process.env.NEXT_PUBLIC_SITE_URL ??
    "https://hcc-compiler-web.vercel.app"
  ).replace(/\/$/, "");
}

export async function POST(
  req: Request,
  ctx: { params: Promise<{ id: string }> },
) {
  const coach = await requireCoach();
  const { id: packId } = await ctx.params;
  const body = (await req.json().catch(() => ({}))) as {
    clientEmail?: string;
    clientFirstName?: string;
    customMessage?: string;
    customSubject?: string;
  };

  if (!body.clientEmail?.trim() || !/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(body.clientEmail)) {
    return NextResponse.json({ error: "valid clientEmail required" }, { status: 400 });
  }

  const ctxData = await loadCoachPackContext(packId, coach.id);
  if (!ctxData) {
    return NextResponse.json({ error: "pack not found" }, { status: 404 });
  }
  const { intakeRow, coachRow, pack } = ctxData;

  if (!coachRow.display_name) {
    return NextResponse.json(
      { error: "coach profile incomplete — set display_name first", redirect: "/account/profile" },
      { status: 412 },
    );
  }

  // 1. Generate (or fetch cached) Schedule.
  try {
    await getOrGenerateSchedule({
      packId,
      intake: intakeRow.payload,
      pack,
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    console.error("[share] schedule generation failed:", msg);
    return NextResponse.json(
      { error: "schedule generation failed", detail: msg },
      { status: 502 },
    );
  }

  const admin = createAdminClient();

  // 2. Mint share token.
  const { data: tokenRow, error: insertErr } = await admin
    .from("share_tokens")
    .insert({
      pack_id: packId,
      coach_id: coach.id,
      client_email: body.clientEmail.trim(),
    })
    .select("id")
    .maybeSingle<{ id: string }>();
  if (insertErr || !tokenRow) {
    return NextResponse.json(
      { error: "failed to mint share token", detail: insertErr?.message },
      { status: 500 },
    );
  }
  const token = tokenRow.id;
  const packUrl = `${appBaseUrl()}/p/${token}`;

  // 3. Send branded email.
  const clientFirstName =
    body.clientFirstName?.trim() ||
    (intakeRow.client_id?.split(/[_\s-]/)[0] ?? "there");

  const { error: emailError } = await sendPlanReadyForClientEmail({
    to: body.clientEmail.trim(),
    coachName: coachRow.display_name,
    coachHeadshotUrl: coachRow.headshot_url,
    clientFirstName,
    packUrl,
    customMessage: body.customMessage,
    customSubject: body.customSubject,
  });

  if (emailError) {
    // Token already exists — return it so coach can copy the link manually.
    return NextResponse.json(
      {
        token,
        packUrl,
        warning: `Email send failed: ${emailError}. The link still works — share it manually.`,
      },
      { status: 207 },
    );
  }

  // 4. Stamp sent_at.
  await admin
    .from("share_tokens")
    .update({ sent_at: new Date().toISOString() })
    .eq("id", token);

  return NextResponse.json({ token, packUrl, sent_to: body.clientEmail.trim() });
}
