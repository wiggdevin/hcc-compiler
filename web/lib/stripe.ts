// Server-only — never import from client components or "use client" files.
// Stripe secret key is read once at module load and never re-exported.

import Stripe from "stripe";

// Lazy singleton — deferred until first request so the build succeeds without
// STRIPE_SECRET_KEY being set in the build environment.
let _stripe: Stripe | undefined;

export function getStripe(): Stripe {
  if (!_stripe) {
    const key = process.env.STRIPE_SECRET_KEY;
    if (!key) throw new Error("STRIPE_SECRET_KEY env var is not set");
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    _stripe = new Stripe(key, { apiVersion: "2026-04-22.dahlia" as any, typescript: true });
  }
  return _stripe;
}

// Back-compat named export so callers can do `stripe.checkout...` as before.
export const stripe = new Proxy({} as Stripe, {
  get(_target, prop) {
    return (getStripe() as unknown as Record<string | symbol, unknown>)[prop];
  },
});

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Return the Stripe customer ID for a coach, creating one if it doesn't exist.
 * Stores the mapping via the `metadata.coach_id` field so we can look it up
 * from webhook events without a Supabase query.
 */
export async function getOrCreateCustomer(
  coachId: string,
  email: string,
): Promise<string> {
  // Search by metadata first to avoid duplicates on re-runs.
  const existing = await stripe.customers.search({
    query: `metadata["coach_id"]:"${coachId}"`,
    limit: 1,
  });

  if (existing.data.length > 0) {
    return existing.data[0].id;
  }

  const customer = await stripe.customers.create({
    email,
    metadata: { coach_id: coachId },
  });

  return customer.id;
}

export type CheckoutPlan = "subscription" | "credits";

interface CheckoutOptions {
  coachId: string;
  email: string;
  plan: CheckoutPlan;
  /** Number of credit packs to purchase (only relevant when plan = 'credits'). Defaults to 1. */
  quantity?: number;
}

/**
 * Create a Stripe Checkout session and return its URL.
 * Subscription → STRIPE_PRICE_ACTIVE_COACH
 * Credits      → STRIPE_PRICE_SINGLE_PLAN_CREDIT (one-time payment)
 */
export async function createCheckoutSession({
  coachId,
  email,
  plan,
  quantity = 1,
}: CheckoutOptions): Promise<string> {
  const appUrl = process.env.NEXT_PUBLIC_APP_URL;
  if (!appUrl) throw new Error("NEXT_PUBLIC_APP_URL env var is not set");

  const customerId = await getOrCreateCustomer(coachId, email);

  if (plan === "subscription") {
    const priceId = process.env.STRIPE_PRICE_ACTIVE_COACH;
    if (!priceId) throw new Error("STRIPE_PRICE_ACTIVE_COACH env var is not set");

    const session = await stripe.checkout.sessions.create({
      customer: customerId,
      mode: "subscription",
      line_items: [{ price: priceId, quantity: 1 }],
      success_url: `${appUrl}/account/billing?session_id={CHECKOUT_SESSION_ID}`,
      cancel_url: `${appUrl}/pricing`,
      subscription_data: {
        metadata: { coach_id: coachId },
      },
      metadata: { coach_id: coachId },
    });

    if (!session.url) throw new Error("Stripe did not return a checkout URL");
    return session.url;
  }

  // one-time credit purchase
  const priceId = process.env.STRIPE_PRICE_SINGLE_PLAN_CREDIT;
  if (!priceId) throw new Error("STRIPE_PRICE_SINGLE_PLAN_CREDIT env var is not set");

  const session = await stripe.checkout.sessions.create({
    customer: customerId,
    mode: "payment",
    line_items: [{ price: priceId, quantity }],
    success_url: `${appUrl}/account/billing?session_id={CHECKOUT_SESSION_ID}`,
    cancel_url: `${appUrl}/pricing`,
    payment_intent_data: {
      metadata: { coach_id: coachId, credit_quantity: String(quantity) },
    },
    metadata: { coach_id: coachId, credit_quantity: String(quantity) },
  });

  if (!session.url) throw new Error("Stripe did not return a checkout URL");
  return session.url;
}

/**
 * Create a Stripe Customer Portal session and return its URL.
 * Allows coaches to manage subscriptions, update payment methods, and view invoices.
 */
export async function createPortalSession(
  coachId: string,
  email: string,
): Promise<string> {
  const appUrl = process.env.NEXT_PUBLIC_APP_URL;
  if (!appUrl) throw new Error("NEXT_PUBLIC_APP_URL env var is not set");

  const customerId = await getOrCreateCustomer(coachId, email);

  const session = await stripe.billingPortal.sessions.create({
    customer: customerId,
    return_url: `${appUrl}/account/billing`,
  });

  return session.url;
}
