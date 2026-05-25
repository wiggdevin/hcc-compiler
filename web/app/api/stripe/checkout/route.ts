import { NextRequest, NextResponse } from "next/server";
import { requireCoach } from "@/lib/auth";
import { createCheckoutSession, type CheckoutPlan } from "@/lib/stripe";

export async function POST(req: NextRequest): Promise<NextResponse> {
  const coach = await requireCoach(); // throws redirect to /sign-in if unauthenticated

  let body: unknown;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: "Invalid JSON body" }, { status: 400 });
  }

  const { plan, quantity } = body as { plan?: unknown; quantity?: unknown };

  if (plan !== "subscription" && plan !== "credits") {
    return NextResponse.json(
      { error: "plan must be 'subscription' or 'credits'" },
      { status: 400 },
    );
  }

  const qty =
    plan === "credits"
      ? typeof quantity === "number" && Number.isInteger(quantity) && quantity >= 1
        ? quantity
        : 1
      : undefined;

  try {
    const url = await createCheckoutSession({
      coachId: coach.id,
      email: coach.email ?? "",
      plan: plan as CheckoutPlan,
      quantity: qty,
    });
    return NextResponse.json({ url });
  } catch (err) {
    const message = err instanceof Error ? err.message : "Stripe error";
    console.error("[checkout] createCheckoutSession failed:", message);
    return NextResponse.json({ error: "Failed to create checkout session" }, { status: 500 });
  }
}
