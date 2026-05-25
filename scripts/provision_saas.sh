#!/usr/bin/env bash
# Idempotent provisioning script for hcc-compiler SaaS surface.
# Run AFTER the Supabase placeholder is deleted from the dashboard
# (free-tier 2-active-project limit blocker).
#
# Usage:
#   bash scripts/provision_saas.sh
#
# Reads from zsvault:
#   - supabase_access_token  (already there)
#   - resend_api_key         (already there)
#   - vercel_token           (already there)
#
# Prompts (interactive, one-time) for:
#   - Stripe secret key (user must create Stripe account first)
#   - Fly auth (one-time `fly auth login` if not authed)
set -euo pipefail
cd "$(dirname "$0")/.."

log() { printf "\033[1;36m[%s]\033[0m %s\n" "$(date +%H:%M:%S)" "$*"; }
die() { printf "\033[1;31m[fail]\033[0m %s\n" "$*" >&2; exit 1; }

# --- 0. Sanity ----------------------------------------------------
command -v supabase >/dev/null || die "supabase CLI missing"
command -v vercel   >/dev/null || die "vercel CLI missing"
command -v fly      >/dev/null || die "fly CLI missing"
command -v zsvault  >/dev/null || die "zsvault CLI missing"

# --- 1. Supabase project ----------------------------------------
# This script does NOT auto-create the project — that's the one
# blocked-on-dashboard step. After you create `hcc-compiler` in the
# Supabase dashboard, paste the project ref below and re-run.
SUPABASE_PROJECT_REF="${SUPABASE_PROJECT_REF:-}"
[ -n "$SUPABASE_PROJECT_REF" ] || die "Set SUPABASE_PROJECT_REF=<ref> after creating the project"

log "Linking Supabase project $SUPABASE_PROJECT_REF"
export SUPABASE_ACCESS_TOKEN="$(zsvault get supabase_access_token)"
supabase link --project-ref "$SUPABASE_PROJECT_REF" || true

log "Applying migrations 0001 + 0002"
supabase db push

log "Creating storage buckets (intakes + packs)"
supabase db remote query <<'SQL' || true
insert into storage.buckets (id, name, public) values ('intakes', 'intakes', false) on conflict do nothing;
insert into storage.buckets (id, name, public) values ('packs',   'packs',   false) on conflict do nothing;
SQL

# --- 2. Capture Supabase keys to vault ---------------------------
log "Fetch keys from Supabase dashboard manually + add to vault:"
cat <<EOF
  zsvault add supabase_hcc_url            "https://${SUPABASE_PROJECT_REF}.supabase.co"
  zsvault add supabase_hcc_anon_key       "<anon key from dashboard>"
  zsvault add supabase_hcc_service_role   "<service role from dashboard>"
  zsvault add supabase_hcc_jwt_secret     "<jwt secret from dashboard>"
EOF
read -p "Press enter once keys are in vault..."

# --- 3. Fly compiler-api -----------------------------------------
fly auth whoami >/dev/null 2>&1 || {
  log "Fly not authed. Run \`fly auth login\` then re-run."
  exit 1
}

if ! fly apps list 2>/dev/null | grep -q hcc-compiler-api; then
  log "Launching Fly app"
  fly launch --name hcc-compiler-api --region iad --no-deploy --copy-config --yes \
    --config services/compiler-api/fly.toml || true
fi

log "Setting Fly secrets"
fly secrets set --app hcc-compiler-api \
  SUPABASE_URL="$(zsvault get supabase_hcc_url)" \
  SUPABASE_SERVICE_ROLE_KEY="$(zsvault get supabase_hcc_service_role)" \
  SUPABASE_JWT_SECRET="$(zsvault get supabase_hcc_jwt_secret)" \
  COMPILER_API_TOKEN="$(openssl rand -hex 32)"

log "Deploying compiler-api"
fly deploy --app hcc-compiler-api \
  --config services/compiler-api/fly.toml \
  --dockerfile services/compiler-api/Dockerfile

COMPILER_API_URL="https://hcc-compiler-api.fly.dev"
COMPILER_API_TOKEN="$(fly secrets list --app hcc-compiler-api | grep COMPILER_API_TOKEN | awk '{print $3}')"

# --- 4. Stripe products ------------------------------------------
log "Stripe products — run these via Stripe dashboard or CLI:"
cat <<EOF
  Product 1: "Active Coach"        recurring \$79/mo
  Product 2: "Single Plan Credit"  one-time  \$29
  Webhook endpoint: https://hcc-compiler-web.vercel.app/api/webhooks/stripe
  Events: checkout.session.completed, customer.subscription.{updated,deleted}, invoice.payment_failed

  Then save to vault:
    zsvault add stripe_hcc_secret_key       "<sk_...>"
    zsvault add stripe_hcc_webhook_secret   "<whsec_...>"
    zsvault add stripe_price_active_coach   "<price_...>"
    zsvault add stripe_price_single_credit  "<price_...>"
EOF
read -p "Press enter once Stripe is configured + values in vault..."

# --- 5. Vercel env vars + deploy ---------------------------------
cd web
export VERCEL_TOKEN="$(zsvault get vercel_token)"

if [ ! -f .vercel/project.json ]; then
  log "Linking Vercel project"
  vercel link --yes --project hcc-compiler-web --token "$VERCEL_TOKEN"
fi

log "Setting Vercel env vars (production)"
set_env() {
  echo "$2" | vercel env add "$1" production --token "$VERCEL_TOKEN" --force >/dev/null 2>&1 || true
}
set_env NEXT_PUBLIC_SUPABASE_URL          "$(zsvault get supabase_hcc_url)"
set_env NEXT_PUBLIC_SUPABASE_ANON_KEY     "$(zsvault get supabase_hcc_anon_key)"
set_env SUPABASE_SERVICE_ROLE_KEY         "$(zsvault get supabase_hcc_service_role)"
set_env COMPILER_API_URL                  "$COMPILER_API_URL"
set_env COMPILER_API_TOKEN                "$COMPILER_API_TOKEN"
set_env STRIPE_SECRET_KEY                 "$(zsvault get stripe_hcc_secret_key)"
set_env STRIPE_WEBHOOK_SECRET             "$(zsvault get stripe_hcc_webhook_secret)"
set_env STRIPE_PRICE_ACTIVE_COACH         "$(zsvault get stripe_price_active_coach)"
set_env STRIPE_PRICE_SINGLE_PLAN_CREDIT   "$(zsvault get stripe_price_single_credit)"
set_env NEXT_PUBLIC_APP_URL               "https://hcc-compiler-web.vercel.app"
set_env RESEND_API_KEY                    "$(zsvault get resend_api_key)"
set_env RESEND_FROM                       "hcc@zerosumsolutions.com"
set_env INTERNAL_API_SECRET               "$(openssl rand -hex 32)"

log "Deploying to Vercel"
vercel --prod --token "$VERCEL_TOKEN"

log "Done. Visit https://hcc-compiler-web.vercel.app"
