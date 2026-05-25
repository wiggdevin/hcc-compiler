import { NextRequest, NextResponse } from "next/server";
import { requireCoach } from "@/lib/auth";
import { createPortalSession } from "@/lib/stripe";

// POST /api/stripe/portal — returns the Stripe Customer Portal URL.
// No body required; coach identity comes from the session.
export async function POST(_req: NextRequest): Promise<NextResponse> {
  const coach = await requireCoach();

  try {
    const url = await createPortalSession(coach.id, coach.email ?? "");
    return NextResponse.json({ url });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Stripe error";
    console.error("[portal] createPortalSession failed:", message);
    return NextResponse.json({ error: "Failed to create portal session" }, { status: 500 });
  }
}
