# Aura Clinic — hcc-compiler frontend

Read-only client-plan navigator + Phase 4 billing. Next.js 16 + Tailwind v4 + Framer Motion + Lucide + Stripe.

## Run

```bash
cd web
pnpm install     # only once
pnpm dev         # http://localhost:3000
```

Loads compiled plans from `../docs/examples/sp2/*.json` and intakes from `../tests/fixtures/intakes/*.yaml` via Server Components at request time.

## Phase 4 — Billing env vars

These must be set in Vercel (or `.env.local` for development). Never commit to the repo.

```
STRIPE_SECRET_KEY                # sk_live_… or sk_test_…
STRIPE_WEBHOOK_SECRET            # whsec_… (from Stripe Dashboard > Webhooks)
STRIPE_PRICE_ACTIVE_COACH        # price_… for the $79/mo subscription
STRIPE_PRICE_SINGLE_PLAN_CREDIT  # price_… for the $29 one-time credit
NEXT_PUBLIC_APP_URL              # https://yourdomain.com (no trailing slash)
```

The other-subagent auth files also require:
```
NEXT_PUBLIC_SUPABASE_URL
NEXT_PUBLIC_SUPABASE_ANON_KEY
SUPABASE_SERVICE_ROLE_KEY
```

## Stripe products to create in the Dashboard

**Product 1 — Active Coach**
- Type: Recurring
- Price: $79.00 USD / month
- Price ID → set as `STRIPE_PRICE_ACTIVE_COACH`
- Price metadata: `plan = active_coach` (used by webhook to populate `subscriptions.plan`)

**Product 2 — Single Plan Credit**
- Type: One-time
- Price: $29.00 USD
- Price ID → set as `STRIPE_PRICE_SINGLE_PLAN_CREDIT`
- Price metadata: `plan = single_plan_credit`

**Webhook endpoint**
- URL: `https://<your-domain>/api/webhooks/stripe`
- Events to listen for:
  - `checkout.session.completed`
  - `customer.subscription.updated`
  - `customer.subscription.deleted`
  - `invoice.payment_failed`
- Copy the signing secret → set as `STRIPE_WEBHOOK_SECRET`

## Compile gate — add to `web/app/api/intakes/[id]/compile/route.ts`

The compile route is owned by the other subagent. Main session must add the following
check near the top of the POST handler, after `requireCoach()` resolves:

```ts
import { canCompile, consumeCredit } from "@/lib/billing";

// Inside the POST handler, after: const coach = await requireCoach();
const billing = await canCompile(coach.id);
if (!billing.ok) {
  return NextResponse.json({ error: billing.reason }, { status: 402 });
}

// ... run the actual compile ...

// After compile succeeds, consume a credit if the coach is on pay-per-use:
if (billing.remaining !== undefined) {
  await consumeCredit(coach.id);
}
```

HTTP 402 Payment Required is the correct status for a billing denial.

## Routes

| Path | Surface |
|---|---|
| `/clients/<id>/intake` | Captured intake — anthropometrics, regimen, constraints |
| `/clients/<id>/overview` | Plan confidence score ring · safety preflight · 6 domain tiles |
| `/clients/<id>/diet` | Nutrition patterns + atoms |
| `/clients/<id>/workout` | Training + conditioning |
| `/clients/<id>/recovery` | Recovery + supplements + behavioral |
| `/clients/<id>/literature` | Deduped citation index with existence + faithfulness verdicts |

`<id>` is one of: `amy`, `carl`, `sam`, `bradley`, `david`, `jackson`, `sarah`, `sebastian`, `tori` (see `lib/data/personas.ts`).

## Architecture

- **`lib/data/types.ts`** — TS mirror of `EvidencePack` (`src/hcc_compiler/sp2/pack.py`)
- **`lib/data/loader.ts`** — `loadEvidencePack`, `loadIntake` (cached per request)
- **`lib/scoring.ts`** — confidence + citation-integrity formulas
- **`components/glass-card.tsx`** — gradient-border shell, used everywhere

If `pack.py` schema drifts, hand-update `types.ts` to match.
