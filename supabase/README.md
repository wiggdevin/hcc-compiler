# Supabase setup for hcc-compiler

## Required environment variables

### Vercel (Next.js web)

| Variable | Where to get it |
|---|---|
| `NEXT_PUBLIC_SUPABASE_URL` | Supabase Dashboard > Settings > API > Project URL |
| `NEXT_PUBLIC_SUPABASE_ANON_KEY` | Supabase Dashboard > Settings > API > anon public key |
| `SUPABASE_SERVICE_ROLE_KEY` | Supabase Dashboard > Settings > API > service_role secret — **never expose to browser** |
| `COMPILER_API_URL` | URL of the deployed FastAPI sidecar, e.g. `https://hcc-compiler-api.fly.dev` |
| `COMPILER_API_TOKEN` | Short-lived JWT or shared secret used to authenticate calls to the compiler API |
| `NEXT_PUBLIC_APP_URL` | Public URL of the web app, e.g. `https://hccompiler.com` or `http://localhost:3010` in dev |

Set these in Vercel Dashboard > Project > Settings > Environment Variables.
For local dev, copy `.env.local.example` to `.env.local` and fill in values.

## Provisioning a new Supabase project

```bash
# 1. Create project at https://app.supabase.com — note the project URL and keys.

# 2. (Optional) install Supabase CLI
brew install supabase/tap/supabase

# 3. Link the project
supabase link --project-ref <your-project-ref>

# 4. Run the migration
supabase db push
# OR paste the contents of migrations/0001_initial.sql in Dashboard > SQL editor and run.

# 5. Create storage buckets (CLI)
supabase storage create intakes --public false
supabase storage create packs   --public false

# 6. Enable storage RLS
# The migration already adds the policies for storage.objects.
# Verify in Dashboard > Storage > Policies.

# 7. Enable Auth providers
# Dashboard > Authentication > Providers:
#   - Email: enabled, "Confirm email" OFF (magic-link is OTP, no confirm step needed)
#   - Google: enable and paste Google OAuth client_id + secret (Phase 5)

# 8. Set the redirect URL
# Dashboard > Authentication > URL Configuration:
#   Site URL: https://hccompiler.com  (or http://localhost:3010 for dev)
#   Additional redirect URLs: https://hcc-compiler.vercel.app
```
