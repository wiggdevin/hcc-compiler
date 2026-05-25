// Service-role Supabase client — server-only.
// Bypasses RLS. Never import this in Client Components or expose to the browser.
//
// Exports:
//   createAdminClient()       — canonical name
//   getSupabaseAdminClient()  — alias used by billing subagent files
import { createClient as createSupabaseClient } from "@supabase/supabase-js";

export function createAdminClient() {
  if (typeof window !== "undefined") {
    throw new Error("createAdminClient() must only be called on the server.");
  }
  return createSupabaseClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.SUPABASE_SERVICE_ROLE_KEY!,
    { auth: { persistSession: false, autoRefreshToken: false } },
  );
}

// Alias used by the Stripe/billing subagent files.
export const getSupabaseAdminClient = createAdminClient;
