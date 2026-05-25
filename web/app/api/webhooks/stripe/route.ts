// Stripe webhook handler. UNAUTHENTICATED — Stripe signs the payload.
// Use raw text body for signature verification (req.text(), NOT req.json()).
// Every event is persisted to billing_events for idempotency and auditability.

import { NextRequest, NextResponse } from "next/server";
import Stripe from "stripe";
import { stripe } from "@/lib/stripe";
import { getSupabaseAdminClient } from "@/lib/supabase/admin";

// App Router reads the raw body via req.text() natively — no config needed.
export const dynamic = "force-dynamic";

export async function POST(req: NextRequest): Promise<NextResponse> {
  const sig = req.headers.get("stripe-signature");
  if (!sig) {
    return NextResponse.json({ error: "Missing stripe-signature header" }, { status: 400 });
  }

  const webhookSecret = process.env.STRIPE_WEBHOOK_SECRET;
  if (!webhookSecret) {
    console.error("[webhook] STRIPE_WEBHOOK_SECRET is not set");
    return NextResponse.json({ error: "Webhook secret not configured" }, { status: 500 });
  }

  // Read raw body as text — required for Stripe signature verification.
  const rawBody = await req.text();

  let event: Stripe.Event;
  try {
    event = stripe.webhooks.constructEvent(rawBody, sig, webhookSecret);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown error";
    console.error("[webhook] signature verification failed:", message);
    return NextResponse.json({ error: "Invalid signature" }, { status: 400 });
  }

  const admin = getSupabaseAdminClient();

  // Idempotency: insert the event record. If stripe_event_id already exists,
  // Postgres unique constraint causes an error — treat that as "already processed".
  const { error: insertError } = await admin.from("billing_events").insert({
    stripe_event_id: event.id,
    event_type: event.type,
    payload: JSON.parse(rawBody) as Record<string, unknown>,
    coach_id: extractCoachId(event) ?? null,
  });

  if (insertError) {
    if (insertError.code === "23505") {
      // Unique violation — already processed. Return 200 so Stripe stops retrying.
      return NextResponse.json({ received: true, skipped: true });
    }
    console.error("[webhook] failed to insert billing_event:", insertError.message);
    // Return 500 so Stripe retries.
    return NextResponse.json({ error: "DB write failed" }, { status: 500 });
  }

  // Dispatch to event-specific handler. Errors here are logged but we still
  // return 200 because the event was persisted — a separate reconciler can
  // replay from billing_events if needed.
  try {
    await dispatch(event, admin);
  } catch (err) {
    const message = err instanceof Error ? err.message : "Unknown";
    console.error(`[webhook] dispatch failed for ${event.type} / ${event.id}:`, message);
    // Still return 200: event is in billing_events; operator can reconcile.
  }

  return NextResponse.json({ received: true });
}

// ---------------------------------------------------------------------------
// Event dispatch
// ---------------------------------------------------------------------------

type AdminClient = ReturnType<typeof getSupabaseAdminClient>;

async function dispatch(event: Stripe.Event, admin: AdminClient): Promise<void> {
  switch (event.type) {
    case "checkout.session.completed":
      await handleCheckoutCompleted(event.data.object as Stripe.Checkout.Session, admin);
      break;
    case "customer.subscription.updated":
      await handleSubscriptionUpdated(event.data.object as Stripe.Subscription, admin);
      break;
    case "customer.subscription.deleted":
      await handleSubscriptionDeleted(event.data.object as Stripe.Subscription, admin);
      break;
    case "invoice.payment_failed":
      await handleInvoicePaymentFailed(event.data.object as Stripe.Invoice, admin);
      break;
    default:
      // Unhandled event types are fine — we log them but don't error.
      break;
  }
}

async function handleCheckoutCompleted(
  session: Stripe.Checkout.Session,
  admin: AdminClient,
): Promise<void> {
  const coachId = session.metadata?.coach_id;
  if (!coachId) {
    console.warn("[webhook] checkout.session.completed missing coach_id metadata");
    return;
  }

  if (session.mode === "subscription" && session.subscription) {
    // Fetch the full subscription object to get period_end and status.
    const sub = await stripe.subscriptions.retrieve(
      typeof session.subscription === "string"
        ? session.subscription
        : session.subscription.id,
    );

    await upsertSubscription(coachId, session.customer as string, sub, admin);
  } else if (session.mode === "payment") {
    // One-time credit purchase. Quantity is stored in session metadata.
    const qty = parseInt(session.metadata?.credit_quantity ?? "1", 10) || 1;
    await incrementCredits(coachId, qty, admin);
  }
}

async function handleSubscriptionUpdated(
  sub: Stripe.Subscription,
  admin: AdminClient,
): Promise<void> {
  const coachId = sub.metadata?.coach_id;
  if (!coachId) {
    // Fallback: look up coach by stripe_customer_id.
    const found = await findCoachByCustomer(sub.customer as string, admin);
    if (!found) {
      console.warn("[webhook] subscription.updated: no coach_id found for customer", sub.customer);
      return;
    }
    await upsertSubscription(found, sub.customer as string, sub, admin);
    return;
  }
  await upsertSubscription(coachId, sub.customer as string, sub, admin);
}

async function handleSubscriptionDeleted(
  sub: Stripe.Subscription,
  admin: AdminClient,
): Promise<void> {
  const coachId =
    sub.metadata?.coach_id ?? (await findCoachByCustomer(sub.customer as string, admin));
  if (!coachId) {
    console.warn("[webhook] subscription.deleted: no coach found for customer", sub.customer);
    return;
  }

  const { error } = await admin
    .from("subscriptions")
    .update({ status: "canceled", updated_at: new Date().toISOString() })
    .eq("coach_id", coachId);

  if (error) {
    throw new Error(`Failed to cancel subscription row: ${error.message}`);
  }
}

async function handleInvoicePaymentFailed(
  invoice: Stripe.Invoice,
  admin: AdminClient,
): Promise<void> {
  const customerId =
    typeof invoice.customer === "string" ? invoice.customer : invoice.customer?.id;
  if (!customerId) return;

  const coachId = await findCoachByCustomer(customerId, admin);
  if (!coachId) {
    console.warn("[webhook] invoice.payment_failed: no coach found for customer", customerId);
    return;
  }

  const { error } = await admin
    .from("subscriptions")
    .update({ status: "past_due", updated_at: new Date().toISOString() })
    .eq("coach_id", coachId);

  if (error) {
    throw new Error(`Failed to mark subscription past_due: ${error.message}`);
  }
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

async function upsertSubscription(
  coachId: string,
  customerId: string,
  sub: Stripe.Subscription,
  admin: AdminClient,
): Promise<void> {
  // In Stripe SDK v22+, current_period_end lives on SubscriptionItem, not the
  // top-level Subscription. Fall back to billing_cycle_anchor if no item present.
  const firstItem = sub.items.data[0];
  const periodEndTs: number =
    (firstItem as Stripe.SubscriptionItem & { current_period_end?: number })
      ?.current_period_end ?? sub.billing_cycle_anchor;
  const periodEnd = new Date(periodEndTs * 1000).toISOString();
  const plan = (firstItem?.price?.metadata?.plan as string | undefined) ?? "active_coach";

  const { error } = await admin.from("subscriptions").upsert(
    {
      coach_id: coachId,
      stripe_customer_id: customerId,
      stripe_subscription_id: sub.id,
      status: sub.status,
      plan,
      current_period_end: periodEnd,
      cancel_at_period_end: sub.cancel_at_period_end,
      updated_at: new Date().toISOString(),
    },
    { onConflict: "coach_id" },
  );

  if (error) {
    throw new Error(`Failed to upsert subscription: ${error.message}`);
  }
}

async function incrementCredits(
  coachId: string,
  quantity: number,
  admin: AdminClient,
): Promise<void> {
  // Read current balance, then upsert with incremented value.
  // Using a raw RPC would be cleaner but we want to stay close to spec's SQL schema.
  const { data, error: readErr } = await admin
    .from("credits")
    .select("balance")
    .eq("coach_id", coachId)
    .maybeSingle();

  if (readErr) throw new Error(`Failed to read credits: ${readErr.message}`);

  const current = data?.balance ?? 0;

  const { error: upsertErr } = await admin.from("credits").upsert(
    {
      coach_id: coachId,
      balance: current + quantity,
      updated_at: new Date().toISOString(),
    },
    { onConflict: "coach_id" },
  );

  if (upsertErr) throw new Error(`Failed to upsert credits: ${upsertErr.message}`);
}

async function findCoachByCustomer(
  customerId: string,
  admin: AdminClient,
): Promise<string | null> {
  const { data, error } = await admin
    .from("subscriptions")
    .select("coach_id")
    .eq("stripe_customer_id", customerId)
    .maybeSingle();

  if (error) return null;
  return data?.coach_id ?? null;
}

/** Pull coach_id out of the event's top-level metadata if present. */
function extractCoachId(event: Stripe.Event): string | undefined {
  // event.data.object is a wide union; cast through unknown to access metadata safely.
  const obj = event.data.object as unknown as Record<string, unknown>;
  const meta = obj["metadata"] as Record<string, string> | undefined;
  return meta?.["coach_id"];
}
