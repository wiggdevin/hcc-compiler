// Server-only billing gate.
// Called before any compile is attempted to enforce subscription OR credit balance.

import { getSupabaseAdminClient } from "@/lib/supabase/admin";

export interface BillingStatus {
  ok: boolean;
  /** Human-readable reason when ok=false. Safe to surface to the coach. */
  reason?: string;
  /** Remaining credits (defined when coach is on credit-only billing). */
  remaining?: number;
}

/**
 * Check whether a coach is permitted to trigger a compile.
 * Priority order:
 *   1. Active (or trialing) subscription → always ok.
 *   2. Positive credit balance → ok, surface remaining count.
 *   3. Neither → deny with upgrade prompt.
 *
 * Uses the admin client (service role) so RLS doesn't interfere with the read.
 */
export async function canCompile(coachId: string): Promise<BillingStatus> {
  const admin = getSupabaseAdminClient();

  // Run both queries in parallel — no dependency between them.
  const [subResult, creditResult] = await Promise.all([
    admin
      .from("subscriptions")
      .select("status")
      .eq("coach_id", coachId)
      .in("status", ["active", "trialing"])
      .maybeSingle(),
    admin
      .from("credits")
      .select("balance")
      .eq("coach_id", coachId)
      .maybeSingle(),
  ]);

  // Treat DB errors as a denial to avoid silent unlocks on infra failures.
  if (subResult.error) {
    console.error("[billing] subscription lookup error:", subResult.error.message);
    return { ok: false, reason: "Billing check failed. Please try again." };
  }
  if (creditResult.error) {
    console.error("[billing] credit lookup error:", creditResult.error.message);
    return { ok: false, reason: "Billing check failed. Please try again." };
  }

  if (subResult.data) {
    return { ok: true };
  }

  const balance = creditResult.data?.balance ?? 0;
  if (balance > 0) {
    return { ok: true, remaining: balance };
  }

  return {
    ok: false,
    reason:
      "No active subscription or credits. Purchase a plan at /pricing to compile packs.",
  };
}

/**
 * Decrement one credit for the given coach.
 * Only call AFTER canCompile() returned ok=true AND the compile succeeded.
 * Returns false if the credit row had already reached 0 (race condition guard).
 */
export async function consumeCredit(coachId: string): Promise<boolean> {
  const admin = getSupabaseAdminClient();

  const { data, error } = await admin.rpc("consume_credit", {
    p_coach_id: coachId,
  });

  if (error) {
    console.error("[billing] consume_credit RPC error:", error.message);
    return false;
  }

  return data === true;
}
