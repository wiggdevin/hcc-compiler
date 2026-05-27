// Public share-token loader used by /p/[token]/* routes.
//
// Service-role read (bypasses RLS) once the token validity is confirmed.
// Returns 404 for unknown / expired / revoked tokens.

import { notFound } from "next/navigation";
import { cache } from "react";
import { createAdminClient } from "@/lib/supabase/admin";
import type { EvidencePack, ClientIntake } from "./types";

export interface CoachBrand {
  display_name: string;
  practice_name: string | null;
  headshot_url: string | null;
  contact_label: string | null;
  contact_url: string | null;
}

export interface ShareView {
  token: string;
  pack: EvidencePack;
  intake: ClientIntake;
  coach: CoachBrand;
  clientLabel: string;
  sentAt: string | null;
}

const UUID_RE =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;

export const loadShare = cache(async (token: string): Promise<ShareView> => {
  if (!UUID_RE.test(token)) notFound();
  const admin = createAdminClient();

  const { data: shareRow } = await admin
    .from("share_tokens")
    .select(
      "id, pack_id, coach_id, expires_at, revoked_at, sent_at",
    )
    .eq("id", token)
    .maybeSingle<{
      id: string;
      pack_id: string;
      coach_id: string;
      expires_at: string | null;
      revoked_at: string | null;
      sent_at: string | null;
    }>();
  if (!shareRow) notFound();
  if (shareRow.revoked_at) notFound();
  if (shareRow.expires_at && new Date(shareRow.expires_at) < new Date()) {
    notFound();
  }

  const [{ data: packRow }, { data: coachRow }] = await Promise.all([
    admin
      .from("packs")
      .select("intake_id, json_path")
      .eq("id", shareRow.pack_id)
      .maybeSingle<{ intake_id: string; json_path: string }>(),
    admin
      .from("coaches")
      .select(
        "display_name, practice_name, headshot_url, contact_label, contact_url",
      )
      .eq("id", shareRow.coach_id)
      .maybeSingle<CoachBrand>(),
  ]);
  if (!packRow || !coachRow) notFound();

  const { data: intakeRow } = await admin
    .from("intakes")
    .select("payload, client_id")
    .eq("id", packRow.intake_id)
    .maybeSingle<{ payload: ClientIntake; client_id: string }>();
  if (!intakeRow) notFound();

  const { data: blob, error: dlError } = await admin.storage
    .from("packs")
    .download(packRow.json_path);
  if (dlError || !blob) notFound();

  const pack = JSON.parse(await blob.text()) as EvidencePack;

  return {
    token,
    pack,
    intake: intakeRow.payload,
    coach: coachRow,
    clientLabel: intakeRow.client_id ?? "your plan",
    sentAt: shareRow.sent_at,
  };
});
