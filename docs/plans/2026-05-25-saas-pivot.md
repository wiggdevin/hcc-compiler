# hcc-compiler → SaaS — Paying-Customer Launch Plan

> **Created:** 2026-05-25
> **Trigger:** Engine cleared the Phase E qualitative coach-grade gate post-personalization (Carl 24/25, Tori 22/25, Sarah 24/25). Original wedge directive said NO SaaS work until engine was excellent. The gate now says it is.
> **Scope:** Take hcc-compiler from CLI tool → product coaches pay for.

---

## Goal

A coach signs up, fills an intake form, gets a personalized evidence pack (JSON + Markdown + PDF), pays via Stripe. End-to-end web flow, no terminal required.

Acceptance: 5 paid sign-ups in the first month from the existing health-coach network.

---

## Stack alignment (decided)

| Layer | Choice | Why |
|---|---|---|
| Web | Next.js 16 in `web/` (already exists) | Aura Clinic v1 already shipped — extend, don't rebuild |
| Compiler | Python in `src/hcc_compiler/` | Stays as-is; expose via HTTP API |
| API for compiler | FastAPI sidecar (new) — `services/compiler-api/` | Wraps `compile()` behind POST /compile; same repo |
| DB | Supabase (`hcc-compiler` project, new) | Matches Devin's stack (zss_intakes lives in shared reaper-console; this gets its own project) |
| Auth | Supabase Auth (email magic-link + Google OAuth) | Standard for coach SaaS; no password fatigue |
| File storage | Supabase Storage (generated MDs + PDFs) | Same project, signed URLs for download |
| Payments | Stripe — subscription tier + credits | Subscription for active coaches; credits for clients ordering individual plans |
| Web deploy | Vercel | Already aligned with Next.js 16 |
| Compiler deploy | Fly.io or Render | Python service with persistent SQLite library DB; Vercel can't run the compiler |
| LLM proxy | `zs-anthropic-proxy` at :11455 — front it via Cloudflare Tunnel `hcc.zerosumsolutions.com` | Same trick used for ScriptCompass (`zsa-tutor.zerosumsolutions.com`); subscription billing only |
| Email | Resend | Magic-link delivery + plan-ready notifications |
| Domain | `hccompiler.com` or under `zerosumsolutions.com` | TBD when this phase starts |

---

## Phase 1 — Hosted intake form (1 week)

Replace hand-edited YAML with a form. Compiler stays local-only for now; admin manually triggers compile after intake submission.

### 1.1 Intake schema → form

Read `src/hcc_compiler/sp2/intake.py` (ClientIntake pydantic model). Generate a JSON Schema (or use Zod re-derivation in `web/lib/intake-schema.ts`). Build a multi-step form in `web/app/(coach)/new-client/page.tsx`:

1. Demographics (sex, age, weight, height, training status)
2. Goals (multiselect chips)
3. Constraints (typed list: injury, dietary, schedule, other — each with detail textarea)
4. Contraindications (typed list)
5. Current regimen (long-form textarea)
6. Optional: metabolic_calibration

Submit → POST to `/api/intakes` → writes a row to `public.intakes` in the new Supabase project + writes the YAML to Supabase Storage at `intakes/<client_id>.yaml`.

### 1.2 Admin dashboard

`web/app/(admin)/intakes/page.tsx` — list pending intakes with a "Compile" button. Click → POST to compiler-api `/compile` (Phase 2) OR for now: copies YAML to clipboard for manual `python scripts/compile_plan.py` run on Devin's local machine, then upload result back via "Upload compiled pack" form.

### 1.3 Pack viewer (coach-facing)

Re-use existing Aura Clinic web at `web/app/clients/[id]/overview/page.tsx`. Switch data source from `docs/examples/sp2/<id>.json` to Supabase Storage read.

### 1.4 Acceptance

- Coach can fill the intake form and submit
- Devin can see the intake in admin dashboard
- Devin can manually compile + upload the result
- Coach can view + download MD/JSON/PDF

---

## Phase 2 — Cloud-deployed compiler API (1 week)

### 2.1 FastAPI sidecar

New service at `services/compiler-api/` (in this repo, separate package):
- `POST /compile` — accepts intake JSON or YAML body, returns `{json: ..., md: ...}` or a job ID for async
- `GET /healthz`, `GET /library/version`
- Auth: signed JWT from Supabase
- Loads `library.db` at startup; rebuilds when a new admin upload arrives

### 2.2 Deploy to Fly.io

- Fly volume for `library.db` (SQLite + embeddings file)
- `Dockerfile`: Python 3.13 + `pip install -e .` from repo root + start FastAPI
- Env: ANTHROPIC_BASE_URL=http://internal-proxy or cloudflared tunnel back to home machine for now
- Cost: ~$5/mo at small instance, scales 0→1 cold

### 2.3 Web → Compiler API

Replace the "Devin manually compiles" step with `web/app/api/intakes/[id]/compile/route.ts` → forwards to compiler-api, persists result to Supabase Storage + DB row update.

### 2.4 Acceptance

- Intake submission triggers compile within 60s end-to-end
- All 9 existing fixture personas compile successfully on the deployed service
- Library version surfaced in the web UI

---

## Phase 3 — Auth + multi-coach (1 week)

### 3.1 Supabase Auth

- Magic-link sign-in
- Google OAuth
- One row in `public.coaches` per user (auto-created on first sign-in)
- RLS policies on `intakes` + `packs`: only the owning coach sees their data

### 3.2 Onboarding flow

`/sign-in` → `/onboarding` (profile + practice name + specialty) → `/dashboard`

### 3.3 Coach dashboard

`web/app/(coach)/dashboard/page.tsx`:
- List of clients (intakes + their packs)
- "New client" CTA → opens the Phase 1 form
- Click client → opens the existing pack viewer

### 3.4 Acceptance

- 2+ test coaches can each sign up and only see their own clients' data
- RLS verified by attempting cross-coach reads (must 401/403)

---

## Phase 4 — Billing (1 week)

### 4.1 Stripe products

- **Active Coach** — $79/mo subscription, unlimited intakes + compiles
- **Single Plan** — $29 per pack credit, no subscription required (low-friction try-it tier)

### 4.2 Integration

- Stripe Checkout for new subscriptions + credit purchases
- Stripe webhooks → write to `public.subscriptions` and `public.credits`
- Compiler API rejects compile requests if no active sub + no credits

### 4.3 Customer portal

Stripe Customer Portal embed at `/account/billing` — cancel sub, update card, see invoices.

### 4.4 Acceptance

- $0.50 Stripe test charge clears end-to-end
- Cancellation flows correctly (active sub stays active until period ends, no immediate compile-block)
- Credit purchase + use round-trips

---

## Phase 5 — Polish + launch (1 week)

### 5.1 Marketing site

`web/app/(marketing)/page.tsx`:
- Hero: "Evidence-backed nutrition + training plans in 60 seconds"
- "How it works" (3 steps with screenshots from Aura Clinic)
- Pricing comparison table
- Testimonial(s) from 1-2 beta coaches
- FAQ + sample pack download (PDF of Carl persona)

### 5.2 PDF export

`/api/packs/[id]/pdf` — Puppeteer or Playwright render → PDF. Same content as Markdown export + print stylesheet, branded letterhead.

### 5.3 Onboarding nudges

Email sequence (Resend):
- Day 0: welcome + watch 90s demo
- Day 1: "Try with a real client this week"
- Day 7: "Need a hand?" with calendar link to Devin
- Day 14: discount code if no paid intake yet

### 5.4 Acceptance

- 5 real coaches sign up in the first 2 weeks of soft launch
- 3 paid plans purchased
- 1 retained subscription at end of month 1

---

## Hard scope guardrails

- **NO** rewrite of compile.py, render.py, library, or atoms. All ship work happens in `web/` + `services/compiler-api/` + Supabase + Stripe.
- **NO** new compiler features ("AI chat with the pack", "follow-up plan generation"). Ship the existing engine as-is.
- **NO** multi-tenancy beyond per-coach (skip team / clinic / org features until v2).
- **NO** custom domain emails until launch (Resend default works).
- **Subscription-only LLM billing** (per global rule): Claude via OAuth/proxy, no pay-per-token Anthropic SDK calls from the FastAPI service.
- **Never store** raw 1Password values or `.env` contents anywhere in the repo or Supabase config. Use Vercel/Fly env vars sourced from `zsvault get <id>` at deploy time.

---

## Files / surfaces touched

```
src/hcc_compiler/sp2/intake.py             # READ-ONLY (source of truth for schema)
services/compiler-api/                     # NEW (FastAPI sidecar)
services/compiler-api/Dockerfile           # NEW
services/compiler-api/main.py              # NEW
services/compiler-api/auth.py              # NEW (Supabase JWT verify)
services/compiler-api/fly.toml             # NEW

web/app/(marketing)/                       # NEW (landing + pricing + FAQ)
web/app/(coach)/                           # NEW (dashboard + new-client form)
web/app/(admin)/                           # NEW (admin intake list, dev-only)
web/app/api/intakes/route.ts               # NEW (POST intake → Supabase)
web/app/api/intakes/[id]/compile/route.ts  # NEW (trigger compiler-api)
web/app/api/packs/[id]/pdf/route.ts        # NEW (PDF export)
web/app/api/webhooks/stripe/route.ts       # NEW (subscription/credit webhook)
web/lib/intake-schema.ts                   # NEW (Zod schema mirror of Python pydantic)
web/lib/supabase.ts                        # NEW (client + admin clients)
web/lib/stripe.ts                          # NEW (Stripe client + helpers)
web/lib/intake-yaml.ts                     # NEW (Zod → YAML serializer matching pydantic loader)

supabase/migrations/0001_initial.sql       # NEW (coaches, intakes, packs, subs, credits)
supabase/config.toml                       # NEW
```

---

## Costs (monthly, steady state at 10 paid coaches)

| Item | Estimate |
|---|---|
| Vercel (Next.js) | $20 (Hobby works until traffic; Pro at $20 once needed) |
| Fly.io compiler | $5-10 (shared CPU, 256MB) |
| Supabase | $0 (free tier) → $25 (Pro tier once egress matters) |
| Stripe | 2.9% + $0.30 per transaction (variable) |
| Resend | $0 (free tier 3k/mo) |
| Domain | $12/yr |
| Cloudflare Tunnel | $0 |
| **Total fixed (steady)** | **~$50/mo** before Stripe fees |

Breakeven at 1 active coach sub.

---

## Risks

- **Compiler cold-start latency** on Fly. Mitigation: Fly auto-start with 1 min warm-up, or upgrade to always-on at $15/mo extra.
- **LLM dependency** for `make extract` is offline-only (atom harvest is admin-time, not customer-time). So no SLA risk to coaches.
- **Schema drift** between pydantic and Zod. Mitigation: regenerate `intake-schema.ts` from pydantic via a build step; fail web build if drift.
- **Stripe webhook lost** → coach pays but doesn't unlock. Mitigation: idempotent webhook handler + nightly reconciler job.
- **Supabase row-level security misconfig** could leak coach A's clients to coach B. Mitigation: write RLS tests as part of Phase 3 acceptance; never deploy with RLS disabled.

---

## ASSUMED — challenge if wrong

- **ASSUMED:** Cost target is "low" not "zero" — Devin willing to spend ~$50-80/mo fixed infrastructure on a product expected to pull in 3-figure subscription revenue.
- **ASSUMED:** No clinical liability shielding for now. Disclaimer in the footer: "Not medical advice. Coaches must apply professional judgment. Plans are evidence references, not prescriptions."
- **ASSUMED:** Hosted Postgres (Supabase) is fine for both intake metadata AND the library/embeddings. If embeddings stay in SQLite on Fly volume, the library compile DB is read-only on the compile path.
- **ASSUMED:** PDF export uses Puppeteer at compile time (cached) — re-rendering on demand if MD changes.
- **ASSUMED:** Coaches don't need bulk-import (upload CSV of clients) in v1. Single intake at a time.

---

## Provisioning runbook (manual steps the code can't auto-do)

### Env var inventory (final, all 4 phases)

Web (`web/.env.local` / Vercel project env):
- `NEXT_PUBLIC_SUPABASE_URL`
- `NEXT_PUBLIC_SUPABASE_ANON_KEY`
- `SUPABASE_SERVICE_ROLE_KEY` (server-only, never `NEXT_PUBLIC_*`)
- `COMPILER_API_URL` (Fly app URL)
- `COMPILER_API_TOKEN` (static bearer for inter-service calls, optional if relying on Supabase JWT pass-through)
- `STRIPE_SECRET_KEY`
- `STRIPE_WEBHOOK_SECRET`
- `STRIPE_PRICE_ACTIVE_COACH` (subscription price ID)
- `STRIPE_PRICE_SINGLE_PLAN_CREDIT` (one-time credit pack price ID)
- `NEXT_PUBLIC_APP_URL` (origin for Stripe success/cancel URLs)
- `RESEND_API_KEY`
- `RESEND_FROM` (verified sender email)
- `INTERNAL_API_SECRET` (gates `/api/email/welcome`)
- `ANTHROPIC_BASE_URL` (added 2026-05-27 for client-viewer schedule LLM; default `https://api.z.ai/api/anthropic`)
- `ANTHROPIC_AUTH_TOKEN` (added 2026-05-27; from `zsvault get zai_api_key`)
- `SCHEDULE_MODEL` (added 2026-05-27; default `glm-4.6`)

Compiler API (`services/compiler-api` / Fly secrets):
- `SUPABASE_URL`
- `SUPABASE_SERVICE_ROLE_KEY`
- `SUPABASE_JWT_SECRET` (for verifying coach JWTs passed from web)
- `COMPILER_API_TOKEN` (matches web's COMPILER_API_TOKEN for static-bearer mode)
- `STORAGE_BUCKET_PACKS` (default `packs`)
- `STORAGE_BUCKET_INTAKES` (default `intakes`)

Secrets origin: every value above is generated by the upstream service (Supabase dashboard, Stripe dashboard, Resend dashboard, Fly platform) — pull each into `zsvault` once provisioned, then `vercel env add` and `fly secrets set` reference the vault values. Never hand-edit `~/.config/zs-api-keys.env`.

### Supabase — known blocker

Devin's `vpzwurcxuliwzumdinwn` org currently has 2 active free projects (`scriptcompass`, `reaper-console`) — that's the free-tier limit. Adding `hcc-compiler` requires ONE of:

- **Pause** one of the active projects in the Supabase dashboard (`reaper-console` if no traffic; `scriptcompass` is live). Free, reversible.
- **Upgrade** the org to Pro tier ($25/mo) which removes the 2-project limit.
- **Delete** an inactive project that's no longer needed (`offeafzjrkwqavrhwvqg "wiggdevin's Project"` is INACTIVE and was a placeholder).

Recommended: delete `wiggdevin's Project` (inactive placeholder), then create `hcc-compiler` via `mcp__claude_ai_Supabase__create_project` with `region=us-west-1`, `organization_id=vpzwurcxuliwzumdinwn`.

After project is live:
```bash
# Get connection details
NEXT_PUBLIC_SUPABASE_URL=https://<project-ref>.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=<anon-key from dashboard>
SUPABASE_SERVICE_ROLE_KEY=<service-role-key from dashboard>

# Apply migrations
supabase link --project-ref <project-ref>
supabase db push  # applies 0001_initial.sql + 0002_billing.sql

# Storage buckets (run in SQL editor or via supabase storage CLI)
insert into storage.buckets (id, name, public) values ('intakes', 'intakes', false);
insert into storage.buckets (id, name, public) values ('packs', 'packs', false);
```

### Fly.io compiler API

```bash
fly launch --name hcc-compiler-api --region iad --no-deploy --config services/compiler-api/fly.toml
fly volume create library_data --app hcc-compiler-api --region iad --size 1
fly secrets set --app hcc-compiler-api SUPABASE_JWT_SECRET="$(zsvault get supabase-hcc-jwt-secret)"
fly deploy --app hcc-compiler-api --config services/compiler-api/fly.toml --dockerfile services/compiler-api/Dockerfile --build-context .
```

### Stripe

Provision via Stripe dashboard:
- Product: "Active Coach" — recurring $79/mo → save price ID as `STRIPE_PRICE_ACTIVE_COACH`
- Product: "Single Plan Credit" — one-time $29 → save price ID as `STRIPE_PRICE_SINGLE_PLAN_CREDIT`
- Webhook endpoint: `https://<app-url>/api/webhooks/stripe` listening for `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.payment_failed`. Copy the signing secret to `STRIPE_WEBHOOK_SECRET`.

### Resend

- ✅ Existing verified domain: `zerosumsolutions.com` (Resend domain id `6cf54e2e-8a6b-42ec-ad45-9b3ee0fdce5b`).
- ✅ API key already in vault: `zsvault get resend_api_key` → `RESEND_API_KEY`.
- Plan deviation: original plan called for `hcc.zerosumsolutions.com` subdomain. **Free tier = 1 domain.** Use sender address `hcc@zerosumsolutions.com` (or `noreply@zerosumsolutions.com`) on the existing verified domain instead. No DNS / upgrade work needed.
- Set `RESEND_FROM=hcc@zerosumsolutions.com` in web env.

### Vercel deploy (web)

```bash
cd web
vercel link --project hcc-compiler-web
vercel env add NEXT_PUBLIC_SUPABASE_URL
vercel env add NEXT_PUBLIC_SUPABASE_ANON_KEY
# ... all env vars from web/.env.example
vercel --prod
```

### Cloudflared tunnel for LLM proxy (harvest path, optional)

```bash
cloudflared tunnel route dns zsa-tutor zsa-tutor.zerosumsolutions.com
# Confirm http://127.0.0.1:11455 is exposed via tunnel
# Set ANTHROPIC_BASE_URL=https://zsa-tutor.zerosumsolutions.com on the harvest worker
```

---

## Out of scope for v1

- Mobile app
- Native client-facing app (clients only see PDF the coach hands them)
- Group / clinic / multi-coach team accounts
- API for third-party EMR integration
- Wearable data ingestion
- Plan-versioning / re-plan workflow
- Bulk CSV intake upload
- Custom branding per coach (white-label)
- Affiliate / referral program

Reserve these for v2.
